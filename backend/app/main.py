import os, io, csv, secrets
from pathlib import Path
from datetime import timedelta
from typing import Literal
from fastapi import FastAPI, Request, Response, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, delete, update, func, or_, cast, String
from sqlalchemy.exc import IntegrityError
from .db import db_session, engine
from .models import *
from .schemas import *
from .security import *
from .finance import money, calculate, CATEGORIES
from .planning import get_plan, payload
from .pdf import generate

app = FastAPI(
    title="P4 Consultores",
    version="2.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)


@app.middleware("http")
async def secure_headers(request, call_next):
    response = await call_next(request)
    response.headers.update(
        {
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "same-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
        }
    )
    if PRODUCTION:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    return response


@app.get("/api/health")
def health(db=Depends(db_session)):
    db.execute(select(func.count()).select_from(User))
    return {"status": "ok"}


@app.post("/api/auth/login")
def login(data: Login, response: Response, request: Request, db=Depends(db_session)):
    keys = sorted(
        [
            digest("account:" + data.phone),
            digest("ip:" + (request.client.host if request.client else "unknown")),
        ]
    )
    attempts = []
    # Create counters atomically, then lock in stable order to serialize concurrent failures.
    for key in keys:
        if engine.dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import insert
        else:
            from sqlalchemy.dialects.sqlite import insert
        db.execute(
            insert(Attempt)
            .values(key=key, count=0, since=now())
            .on_conflict_do_nothing(index_elements=["key"])
        )
    for key in keys:
        a = db.scalar(select(Attempt).where(Attempt.key == key).with_for_update())
        if aware(a.since) < now() - timedelta(minutes=15):
            a.count = 0
            a.since = now()
        if a.count >= 10:
            db.commit()
            raise HTTPException(429, "Muitas tentativas. Aguarde 15 minutos.")
        attempts.append(a)
    u = db.scalar(select(User).where(User.phone == data.phone))
    valid = check_password(data.password, u.password_hash if u else DUMMY)
    if not u or not valid or not u.enabled:
        for a in attempts:
            a.count += 1
        db.commit()
        raise HTTPException(
            401,
            "Celular ou senha incorretos. Confira o código do país e tente novamente.",
        )
    for a in attempts:
        a.count = 0
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(32)
    db.add(Session(token_hash=digest(token), user_id=u.id, csrf=csrf))
    audit(db, u, u.id, "login")
    db.commit()
    response.set_cookie(
        COOKIE, token, httponly=True, secure=PRODUCTION, samesite="lax", path="/"
    )
    return {"user": public(u), "csrf": csrf}


@app.get("/api/auth/me")
def me(request: Request, u=Depends(current)):
    return {"user": public(u), "csrf": request.state.session.csrf}


@app.post("/api/auth/logout")
def logout(
    request: Request, response: Response, u=Depends(current), db=Depends(db_session)
):
    db.delete(request.state.session)
    db.commit()
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@app.post("/api/auth/password")
def password(
    data: Password, response: Response, u=Depends(current), db=Depends(db_session)
):
    if not check_password(data.old_password, u.password_hash):
        raise HTTPException(400, "Senha atual incorreta.")
    u.password_hash = hash_password(data.password)
    invalidate(db, u.id)
    audit(db, u, u.id, "password_changed")
    db.commit()
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@app.post("/api/auth/recover")
def recover():
    return {
        "message": "O envio automático não está configurado. Contate a equipe para verificar sua identidade e receber um código temporário. Não compartilhe sua senha."
    }


@app.post("/api/auth/reset")
def reset(data: ResetInput, db=Depends(db_session)):
    r = db.scalar(
        select(Reset).where(Reset.token_hash == digest(data.token)).with_for_update()
    )
    if not r or aware(r.expires_at) <= now():
        raise HTTPException(400, "Código inválido ou vencido.")
    u = db.get(User, r.user_id)
    u.password_hash = hash_password(data.password)
    invalidate(db, u.id)
    db.execute(delete(Reset).where(Reset.user_id == u.id))
    audit(db, None, u.id, "password_reset")
    db.commit()
    return {"ok": True}


@app.post("/api/users/{sid}/recovery")
def recovery(sid: int, u=Depends(current), db=Depends(db_session)):
    require(u, "administrador")
    if not db.get(User, sid):
        raise HTTPException(404, "Conta não encontrada.")
    token = secrets.token_urlsafe(32)
    db.execute(delete(Reset).where(Reset.user_id == sid))
    db.add(
        Reset(
            token_hash=digest(token),
            user_id=sid,
            expires_at=now() + timedelta(minutes=20),
        )
    )
    audit(db, u, sid, "recovery_issued")
    db.commit()
    return {
        "token": token,
        "message": "Entregue somente após verificação de identidade. Uso único, 20 minutos.",
    }


@app.get("/api/support")
def support(db=Depends(db_session)):
    s = db.get(Setting, "support")
    return {
        "contact": s.value if s else "Suporte ainda não configurado pela administração."
    }


@app.put("/api/support")
def set_support(data: Support, u=Depends(current), db=Depends(db_session)):
    require(u, "administrador")
    db.merge(Setting(key="support", value=data.contact))
    audit(db, u, None, "support_changed")
    db.commit()
    return {"ok": True}


@app.get("/api/users")
def users(
    q: str = Query("", max_length=160),
    status_filter: str = "",
    completion: str = "",
    team: bool = False,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    u=Depends(current),
    db=Depends(db_session),
):
    require(u, "consultor", "administrador", "vendedor")
    stmt = select(User)
    if team:
        require(u, "administrador")
    else:
        stmt = stmt.where(cast(User.roles, String).like('%"aluno"%'))
    if q:
        pattern = (
            "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        )
        stmt = stmt.where(
            or_(
                User.name.ilike(pattern, escape="\\"),
                User.phone.ilike(pattern, escape="\\"),
                User.email.ilike(pattern, escape="\\"),
            )
        )
    if status_filter == "vencido":
        stmt = stmt.where(
            User.status == "ativo",
            or_(User.expires_at == None, User.expires_at <= now()),
        )
    elif status_filter == "ativo":
        stmt = stmt.where(User.status == "ativo", User.expires_at > now())
    elif status_filter:
        stmt = stmt.where(User.status == status_filter)
    if completion:
        require(u, "consultor", "administrador")
        stmt = stmt.outerjoin(Plan, Plan.user_id == User.id)
        if completion == "concluido":
            stmt = stmt.where(func.json_array_length(Plan.completed) == 8)
        else:
            stmt = stmt.where(
                or_(Plan.id == None, func.json_array_length(Plan.completed) < 8)
            )
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    return {
        "items": [
            public(x)
            for x in db.scalars(
                stmt.order_by(User.name, User.id).offset((page - 1) * size).limit(size)
            )
        ],
        "total": total,
        "page": page,
    }


@app.post("/api/users", status_code=201)
def create_user(data: UserInput, u=Depends(current), db=Depends(db_session)):
    require(u, "vendedor", "administrador")
    if "administrador" not in u.roles and data.roles != ["aluno"]:
        raise HTTPException(403, "Vendedor pode apenas pré-cadastrar alunos.")
    item = data.model_dump(exclude={"password"})
    item["roles"] = sorted(set(data.roles))
    target = User(**item, password_hash=hash_password(data.password), status="pendente")
    db.add(target)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Celular já cadastrado.")
    audit(db, u, target.id, "user_created", {"roles": target.roles})
    db.commit()
    return public(target)


@app.put("/api/users/{sid}/roles")
def roles(sid: int, data: Roles, u=Depends(current), db=Depends(db_session)):
    require(u, "administrador")
    target = db.get(User, sid)
    if not target:
        raise HTTPException(404, "Conta não encontrada.")
    if sid == u.id and "administrador" not in data.roles:
        raise HTTPException(400, "Não remova seu próprio perfil administrativo.")
    before = target.roles
    target.roles = sorted(set(data.roles))
    invalidate(db, sid)
    audit(db, u, sid, "roles_changed", {"before": before, "after": target.roles})
    db.commit()
    return public(target)


@app.put("/api/users/{sid}/enabled")
def enabled(sid: int, data: Enabled, u=Depends(current), db=Depends(db_session)):
    require(u, "administrador")
    target = db.get(User, sid)
    if not target:
        raise HTTPException(404, "Conta não encontrada.")
    if sid == u.id and not data.enabled:
        raise HTTPException(400, "Não desative sua própria conta.")
    target.enabled = data.enabled
    invalidate(db, sid)
    audit(db, u, sid, "account_enabled", {"enabled": data.enabled})
    db.commit()
    return public(target)


@app.post("/api/users/{sid}/access")
def access(sid: int, data: Access, u=Depends(current), db=Depends(db_session)):
    require(u, "administrador")
    target = db.scalar(select(User).where(User.id == sid).with_for_update())
    if not target or "aluno" not in target.roles:
        raise HTTPException(404, "Aluno não encontrado.")
    before = {"status": target.status, "expires_at": str(target.expires_at)}
    if data.action in ("ativar", "renovar"):
        base = (
            max(now(), aware(target.expires_at))
            if data.action == "renovar" and target.expires_at
            else now()
        )
        target.expires_at = aware(data.expires_at) if data.expires_at else annual(base)
        if target.expires_at <= now():
            raise HTTPException(422, "Defina uma data futura para o vencimento.")
        target.released_at = target.released_at or now()
        target.status = "ativo"
        for r in db.scalars(
            select(Renewal).where(
                Renewal.student_id == sid, Renewal.status == "pendente"
            )
        ):
            r.status = "aprovada"
    else:
        target.status = "bloqueado" if data.action == "bloquear" else "revogado"
    db.add(
        AccessEvent(
            student_id=sid,
            admin_id=u.id,
            action=data.action,
            expires_at=target.expires_at,
        )
    )
    audit(
        db,
        u,
        sid,
        "access_" + data.action,
        {
            "before": before,
            "after": {"status": target.status, "expires_at": str(target.expires_at)},
        },
    )
    db.commit()
    return public(target)


@app.get("/api/users/{sid}/access-history")
def access_history(sid: int, u=Depends(current), db=Depends(db_session)):
    if sid != u.id:
        require(u, "consultor", "administrador")
    return list(
        db.scalars(
            select(AccessEvent)
            .where(AccessEvent.student_id == sid)
            .order_by(AccessEvent.id.desc())
            .limit(100)
        )
    )


@app.post("/api/renewals")
def renewal(u=Depends(current), db=Depends(db_session)):
    require(u, "aluno")
    db.scalar(select(User).where(User.id == u.id).with_for_update())
    if not db.scalar(
        select(Renewal).where(Renewal.student_id == u.id, Renewal.status == "pendente")
    ):
        db.add(Renewal(student_id=u.id))
        audit(db, u, u.id, "renewal_requested")
    db.commit()
    return {"message": "Solicitação registrada. A renovação depende da administração."}


@app.get("/api/renewals")
def renewal_list(u=Depends(current), db=Depends(db_session)):
    require(u, "administrador")
    return [
        {
            "id": r.id,
            "student_id": r.student_id,
            "name": name,
            "status": r.status,
            "created_at": r.created_at,
        }
        for r, name in db.execute(
            select(Renewal, User.name)
            .join(User, User.id == Renewal.student_id)
            .order_by(Renewal.id.desc())
            .limit(100)
        )
    ]


@app.get("/api/categories")
def categories(u=Depends(current), db=Depends(db_session)):
    if not set(u.roles) & {"consultor", "administrador"}:
        financial(db, u, u.id)
    return CATEGORIES


@app.get("/api/plans/{sid}")
def read_plan(sid: int, u=Depends(current), db=Depends(db_session)):
    financial(db, u, sid)
    return payload(db, get_plan(db, sid))


@app.put("/api/plans/{sid}")
def save_plan(sid: int, data: PlanInput, u=Depends(current), db=Depends(db_session)):
    financial(db, u, sid)
    p = get_plan(db, sid)
    before = payload(db, p)
    result = db.execute(
        update(Plan)
        .where(Plan.id == p.id, Plan.version == data.version)
        .values(
            **data.model_dump(exclude={"entries", "debts", "goals", "version"}),
            version=Plan.version + 1
        )
    )
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(
            409,
            "Outro dispositivo alterou este planejamento. Seus valores continuam na tela. Recarregue os dados antes de editar novamente.",
        )
    for model in (Entry, Debt, Goal):
        db.execute(delete(model).where(model.plan_id == p.id))
    for e in data.entries:
        item = e.model_dump()
        item["forecast"] = money(e.forecast)
        item["actual"] = money(e.actual)
        db.add(Entry(plan_id=p.id, **item))
    for d in data.debts:
        item = d.model_dump()
        item["balance"] = money(d.balance)
        item["end"] = str(d.end) if d.end else None
        db.add(Debt(plan_id=p.id, **item))
    for g in data.goals:
        item = g.model_dump()
        item["amount"] = money(g.amount)
        item["deadline"] = str(g.deadline) if g.deadline else None
        db.add(Goal(plan_id=p.id, **item))
    db.flush()
    db.refresh(p)
    after = payload(db, p)
    audit(db, u, sid, "plan_changed", {"before": before, "after": after})
    db.commit()
    return after


@app.get("/api/reports/{sid}")
def report(
    sid: int,
    mode: Literal["forecast", "actual"] = "forecast",
    u=Depends(current),
    db=Depends(db_session),
):
    student = financial(db, u, sid)
    p = get_plan(db, sid)
    return {
        "student": public(student),
        "generated_at": now(),
        **calculate(
            p, list(db.scalars(select(Entry).where(Entry.plan_id == p.id))), mode
        ),
    }


@app.get("/api/reports/{sid}/pdf")
def pdf(
    sid: int,
    mode: Literal["forecast", "actual"] = "forecast",
    u=Depends(current),
    db=Depends(db_session),
):
    student = financial(db, u, sid)
    p = get_plan(db, sid)
    r = calculate(p, list(db.scalars(select(Entry).where(Entry.plan_id == p.id))), mode)
    notes = list(
        db.scalars(select(Note).where(Note.student_id == sid, Note.internal == False))
    )
    return StreamingResponse(
        generate(student, r, payload(db, p), notes),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="planejamento-p4.pdf"'},
    )


@app.get("/api/notes/{sid}")
def notes(sid: int, u=Depends(current), db=Depends(db_session)):
    financial(db, u, sid)
    stmt = select(Note).where(Note.student_id == sid)
    if not set(u.roles) & {"consultor", "administrador"}:
        stmt = stmt.where(Note.internal == False)
    return list(db.scalars(stmt.order_by(Note.id.desc()).limit(200)))


@app.post("/api/notes/{sid}")
def add_note(sid: int, data: NoteInput, u=Depends(current), db=Depends(db_session)):
    require(u, "consultor", "administrador")
    financial(db, u, sid)
    db.add(Note(student_id=sid, author_id=u.id, **data.model_dump()))
    audit(db, u, sid, "note_created", {"internal": data.internal})
    db.commit()
    return {"ok": True}


@app.get("/api/audit")
def audit_list(
    subject: int | None = None,
    page: int = Query(1, ge=1),
    u=Depends(current),
    db=Depends(db_session),
):
    if subject is None:
        require(u, "administrador")
    else:
        require(u, "consultor", "administrador")
        financial(db, u, subject)
    stmt = select(Audit)
    if subject is not None:
        stmt = stmt.where(Audit.subject == subject)
    return list(
        db.scalars(stmt.order_by(Audit.id.desc()).offset((page - 1) * 20).limit(20))
    )


@app.get("/api/contents")
def content_list(all: bool = False, u=Depends(current), db=Depends(db_session)):
    if all:
        require(u, "administrador")
    elif not set(u.roles) & {"consultor", "administrador"}:
        financial(db, u, u.id)
    stmt = select(Content)
    if not all:
        stmt = stmt.where(Content.status == "publicado")
    return list(db.scalars(stmt.order_by(Content.id).limit(200)))


@app.post("/api/contents")
def create_content(data: ContentInput, u=Depends(current), db=Depends(db_session)):
    require(u, "administrador")
    values = data.model_dump()
    values["version"] = 1
    c = Content(**values, approved_by=u.id if data.status == "publicado" else None)
    db.add(c)
    db.flush()
    db.add(ContentVersion(content_id=c.id, version=1, snapshot=values))
    audit(db, u, None, "content_created", {"id": c.id, "status": c.status})
    db.commit()
    return {"id": c.id}


@app.put("/api/contents/{cid}")
def edit_content(
    cid: int, data: ContentInput, u=Depends(current), db=Depends(db_session)
):
    require(u, "administrador")
    result = db.execute(
        update(Content)
        .where(Content.id == cid, Content.version == data.version)
        .values(
            **data.model_dump(exclude={"version"}),
            version=Content.version + 1,
            approved_by=u.id if data.status == "publicado" else None
        )
    )
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(
            409, "Conteúdo alterado por outra pessoa. Atualize a lista."
        )
    db.add(
        ContentVersion(
            content_id=cid, version=data.version + 1, snapshot=data.model_dump()
        )
    )
    audit(
        db,
        u,
        None,
        "content_changed",
        {"id": cid, "version": data.version + 1, "status": data.status},
    )
    db.commit()
    return {"ok": True}


@app.get("/api/contents/{cid}/versions")
def content_versions(cid: int, u=Depends(current), db=Depends(db_session)):
    require(u, "administrador")
    return list(
        db.scalars(
            select(ContentVersion)
            .where(ContentVersion.content_id == cid)
            .order_by(ContentVersion.version.desc())
        )
    )


@app.post("/api/import")
def import_csv(data: CSVInput, u=Depends(current), db=Depends(db_session)):
    require(u, "administrador")
    rows = []
    seen = set()
    reader = csv.DictReader(io.StringIO(data.text.lstrip("\ufeff")))
    if not {"name", "phone"}.issubset(reader.fieldnames or []):
        raise HTTPException(422, "CSV deve conter name,phone e opcionalmente email.")
    for i, row in enumerate(reader, start=2):
        if i > 5001:
            raise HTTPException(422, "Limite de 5.000 linhas por lote.")
        try:
            item = UserInput(
                name=row.get("name", ""),
                phone=row.get("phone", ""),
                email=row.get("email") or None,
                password=secrets.token_urlsafe(24),
            )
            if item.phone in seen or db.scalar(
                select(User.id).where(User.phone == item.phone)
            ):
                raise ValueError()
            seen.add(item.phone)
            rows.append(
                {
                    "line": i,
                    "valid": True,
                    "name": item.name,
                    "phone": item.phone,
                    "email": item.email,
                }
            )
        except ValueError:
            rows.append(
                {
                    "line": i,
                    "valid": False,
                    "name": row.get("name", ""),
                    "error": "Cadastro inválido ou celular duplicado.",
                }
            )
    invalid = [r["line"] for r in rows if not r["valid"]]
    if data.commit and not invalid:
        for r in rows:
            db.add(
                User(
                    name=r["name"],
                    phone=r["phone"],
                    email=r["email"],
                    password_hash=hash_password(secrets.token_urlsafe(24)),
                    roles=["aluno"],
                    status="pendente",
                )
            )
    audit(
        db,
        u,
        None,
        "csv_commit" if data.commit else "csv_preview",
        {"total": len(rows), "invalid_lines": invalid},
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Cadastro concorrente. Faça uma nova prévia.")
    if data.commit and invalid:
        raise HTTPException(422, "Corrija as linhas inválidas antes de importar.")
    return {
        "rows": rows,
        "committed": data.commit,
        "count": len(rows),
        "message": "Cadastros pendentes; o primeiro acesso exige recuperação controlada.",
    }


@app.delete("/api/users/{sid}")
def delete_user(
    sid: int, data: DeleteInput, u=Depends(current), db=Depends(db_session)
):
    require(u, "administrador")
    target = db.get(User, sid)
    if not target:
        raise HTTPException(404, "Conta não encontrada.")
    if sid == u.id:
        raise HTTPException(400, "Não exclua sua própria conta.")
    if data.confirmation != "EXCLUIR " + target.phone:
        raise HTTPException(
            422, "Confirme com EXCLUIR seguido do celular internacional."
        )
    db.execute(delete(Audit).where(or_(Audit.subject == sid, Audit.actor == sid)))
    db.execute(delete(User).where(User.id == sid))
    audit(db, u, sid, "user_deleted", {"reason": data.reason})
    db.commit()
    return {"ok": True}


DIST = Path(
    os.getenv(
        "FRONTEND_DIST", str(Path(__file__).resolve().parents[2] / "frontend/dist")
    )
)
if DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, "Rota não encontrada.")
        candidate = (DIST / path).resolve()
        if DIST.resolve() in candidate.parents and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(DIST / "index.html")
