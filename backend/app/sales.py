"""Commercial workflow. Financial access is explicit, read-only, and audited."""

import csv, io
from datetime import datetime, timedelta, timezone, date, time
from decimal import Decimal
from zoneinfo import ZoneInfo
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import Field, field_validator, model_validator
from sqlalchemy import select, func, or_, cast, String, delete
from sqlalchemy.exc import IntegrityError
from .db import db_session
from .models import User, Plan, Entry, Note, Opportunity, Appointment
from .schemas import Strict
from .security import current, require, audit, public, now, aware
from .planning import payload
from .finance import calculate, money

router = APIRouter(prefix="/api/sales", tags=["Comercial"])
STAGES = {
    "aguardando": "Aguardando consultoria",
    "agendado": "Consultoria agendada",
    "consultoria": "Consultoria realizada",
    "proposta": "Proposta apresentada",
    "negociacao": "Em negociação",
    "ganho": "Venda registrada",
    "perdido": "Não convertido",
}
Stage = Literal[
    "aguardando",
    "agendado",
    "consultoria",
    "proposta",
    "negociacao",
    "ganho",
    "perdido",
]


def sales_user(u=Depends(current)):
    require(u, "vendedor", "administrador")
    return u


def student(db, sid):
    target = db.get(User, sid)
    if not target or "aluno" not in target.roles:
        raise HTTPException(404, "Aluno não encontrado.")
    return target


def owner(db, uid):
    target = db.get(User, uid)
    if (
        not target
        or not target.enabled
        or not set(target.roles) & {"vendedor", "administrador"}
    ):
        raise HTTPException(422, "Escolha um responsável comercial habilitado.")
    return target


class NewOpportunity(Strict):
    student_id: int
    owner_id: int | None = None


class OpportunityUpdate(Strict):
    version: int = Field(ge=1)
    owner_id: int | None = None
    stage: Stage
    cash_price: str = "5000.00"
    installment_count: int = Field(default=12, ge=1, le=120)
    installment_value: str = "497.00"
    selected_offer: Literal["cash", "installments"] | None = None
    next_contact: datetime | None = None
    notes: str = Field(default="", max_length=10000)
    lost_reason: str = Field(default="", max_length=2000)

    @field_validator("cash_price", "installment_value")
    @classmethod
    def amount(cls, v):
        result = money(v)
        if result is None:
            raise ValueError("Informe o valor da proposta.")
        return str(result)

    @field_validator("next_contact")
    @classmethod
    def zoned(cls, v):
        if v is not None:
            if v.tzinfo is None:
                raise ValueError("Informe data com fuso horário.")
            return v.astimezone(timezone.utc)
        return v

    @model_validator(mode="after")
    def closure(self):
        if self.stage == "ganho":
            if self.selected_offer is None:
                raise ValueError("Escolha a condição aceita para registrar a venda.")
            if (
                money(
                    self.cash_price
                    if self.selected_offer == "cash"
                    else self.installment_value
                )
                <= 0
            ):
                raise ValueError("Informe o valor acordado da venda.")
        return self


class AppointmentInput(Strict):
    opportunity_id: int
    owner_id: int
    starts_at: datetime
    duration_minutes: int = Field(default=45, ge=15, le=180)
    status: Literal[
        "agendada", "confirmada", "realizada", "cancelada", "nao_compareceu"
    ] = "agendada"
    meeting_url: str = Field(default="", max_length=500)
    notes: str = Field(default="", max_length=10000)

    @field_validator("starts_at")
    @classmethod
    def zoned(cls, v):
        if v.tzinfo is None:
            raise ValueError("Informe data com fuso horário.")
        return v.astimezone(timezone.utc)

    @field_validator("meeting_url")
    @classmethod
    def url(cls, v):
        v = v.strip()
        if v:
            from urllib.parse import urlsplit

            p = urlsplit(v)
            if p.scheme != "https" or not p.hostname or p.username or p.password:
                raise ValueError("Use um link de reunião HTTPS válido.")
        return v


class AppointmentUpdate(AppointmentInput):
    version: int = Field(ge=1)


class BulkQueue(Strict):
    confirm: Literal[True]


def serialize_op(db, o):
    s = db.get(User, o.student_id)
    responsible = db.get(User, o.owner_id) if o.owner_id else None
    total = (
        o.cash_price
        if o.selected_offer == "cash"
        else (
            o.installment_value * o.installment_count
            if o.selected_offer == "installments"
            else None
        )
    )
    return {
        "id": o.id,
        "student": public(s),
        "owner_id": o.owner_id,
        "owner_name": responsible.name if responsible else "Sem responsável",
        "stage": o.stage,
        "cash_price": str(o.cash_price),
        "installment_count": o.installment_count,
        "installment_value": str(o.installment_value),
        "installment_total": str(o.installment_value * o.installment_count),
        "selected_offer": o.selected_offer,
        "contract_total": str(total) if total is not None else None,
        "next_contact": o.next_contact,
        "notes": o.notes,
        "lost_reason": o.lost_reason,
        "version": o.version,
        "created_at": o.created_at,
        "updated_at": o.updated_at,
        "closed_at": o.closed_at,
    }


def serialize_appointment(db, a):
    o = db.get(Opportunity, a.opportunity_id)
    s = db.get(User, o.student_id)
    responsible = db.get(User, a.owner_id) if a.owner_id else None
    return {
        "id": a.id,
        "opportunity_id": a.opportunity_id,
        "student_id": s.id,
        "student_name": s.name,
        "student_phone": s.phone,
        "owner_id": a.owner_id,
        "owner_name": responsible.name if responsible else "Responsável removido",
        "starts_at": a.starts_at,
        "ends_at": a.ends_at,
        "duration_minutes": a.duration_minutes,
        "status": a.status,
        "meeting_url": a.meeting_url,
        "notes": a.notes,
        "version": a.version,
    }


@router.get("/settings")
def settings(u=Depends(sales_user)):
    return {
        "stages": STAGES,
        "community_reference": "290.00",
        "default_cash_price": "5000.00",
        "default_installment_count": 12,
        "default_installment_value": "497.00",
        "default_installment_total": "5964.00",
        "duration_minutes": 45,
        "timezone": "America/Sao_Paulo",
    }


@router.get("/owners")
def owners(u=Depends(sales_user), db=Depends(db_session)):
    stmt = (
        select(User)
        .where(
            User.enabled == True,
            or_(
                cast(User.roles, String).like('%"vendedor"%'),
                cast(User.roles, String).like('%"administrador"%'),
            ),
        )
        .order_by(User.name)
    )
    return [{"id": x.id, "name": x.name} for x in db.scalars(stmt)]


@router.post("/queue/sync")
def sync_queue(data: BulkQueue, u=Depends(sales_user), db=Depends(db_session)):
    # Lock a stable administrative row to serialize bulk actions; unique student_id also protects individual additions.
    db.scalar(select(User).where(User.id == u.id).with_for_update())
    ids = list(
        db.scalars(
            select(User.id)
            .where(cast(User.roles, String).like('%"aluno"%'))
            .order_by(User.id)
        )
    )
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert
    from .db import engine

    insert = pg_insert if engine.dialect.name == "postgresql" else sqlite_insert
    created = 0
    for sid in ids:
        result = db.execute(
            insert(Opportunity)
            .values(
                student_id=sid,
                owner_id=None,
                stage="aguardando",
                cash_price=Decimal("5000"),
                installment_count=12,
                installment_value=Decimal("497"),
                notes="",
                lost_reason="",
                version=1,
                created_at=now(),
                updated_at=now(),
            )
            .on_conflict_do_nothing(index_elements=["student_id"])
            .returning(Opportunity.id)
        )
        created += 1 if result.scalar_one_or_none() is not None else 0
    audit(
        db,
        u,
        None,
        "sales_queue_sync",
        {
            "students_considered": len(ids),
            "created": created,
            "existing": len(ids) - created,
        },
    )
    db.commit()
    return {
        "created": created,
        "existing": len(ids) - created,
        "message": "Alunos adicionados à fila comercial. Acesso e dados financeiros não foram alterados.",
    }


@router.post("/opportunities")
def create_opportunity(
    data: NewOpportunity, u=Depends(sales_user), db=Depends(db_session)
):
    student(db, data.student_id)
    db.scalar(select(User).where(User.id == data.student_id).with_for_update())
    existing = db.scalar(
        select(Opportunity).where(Opportunity.student_id == data.student_id)
    )
    if existing:
        return serialize_op(db, existing)
    if data.owner_id:
        owner(db, data.owner_id)
    o = Opportunity(student_id=data.student_id, owner_id=data.owner_id)
    db.add(o)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return serialize_op(
            db,
            db.scalar(
                select(Opportunity).where(Opportunity.student_id == data.student_id)
            ),
        )
    audit(db, u, o.student_id, "sales_opportunity_created", {"opportunity_id": o.id})
    db.commit()
    return serialize_op(db, o)


@router.get("/opportunities")
def list_opportunities(
    q: str = Query("", max_length=160),
    stage: Stage | None = None,
    owner_id: int | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(30, ge=1, le=100),
    u=Depends(sales_user),
    db=Depends(db_session),
):
    stmt = select(Opportunity).join(User, User.id == Opportunity.student_id)
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
    if stage:
        stmt = stmt.where(Opportunity.stage == stage)
    if owner_id:
        stmt = stmt.where(Opportunity.owner_id == owner_id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = list(
        db.scalars(
            stmt.order_by(Opportunity.created_at, Opportunity.id)
            .offset((page - 1) * size)
            .limit(size)
        )
    )
    return {"items": [serialize_op(db, o) for o in rows], "total": total, "page": page}


@router.get("/opportunities/{oid}")
def read_opportunity(oid: int, u=Depends(sales_user), db=Depends(db_session)):
    o = db.get(Opportunity, oid)
    if not o:
        raise HTTPException(404, "Oportunidade não encontrada.")
    return serialize_op(db, o)


@router.put("/opportunities/{oid}")
def edit_opportunity(
    oid: int, data: OpportunityUpdate, u=Depends(sales_user), db=Depends(db_session)
):
    o = db.scalar(select(Opportunity).where(Opportunity.id == oid).with_for_update())
    if not o:
        raise HTTPException(404, "Oportunidade não encontrada.")
    if o.version != data.version:
        raise HTTPException(
            409,
            "Oportunidade alterada por outra pessoa. Reabra o atendimento antes de salvar.",
        )
    if data.owner_id:
        owner(db, data.owner_id)
    before = serialize_op(db, o)
    old_stage = o.stage
    for key, value in data.model_dump(exclude={"version"}).items():
        setattr(
            o,
            key,
            money(value) if key in ("cash_price", "installment_value") else value,
        )
    if o.stage in ("ganho", "perdido") and old_stage != o.stage:
        o.closed_at = now()
    elif o.stage not in ("ganho", "perdido"):
        o.closed_at = None
    o.version += 1
    o.updated_at = now()
    # Encode timestamps explicitly in audit JSON.
    from fastapi.encoders import jsonable_encoder

    audit(
        db,
        u,
        o.student_id,
        "sales_opportunity_changed",
        {
            "before": jsonable_encoder(before),
            "after": jsonable_encoder(serialize_op(db, o)),
        },
    )
    db.commit()
    return serialize_op(db, o)


@router.get("/financial/{sid}")
def read_financial(sid: int, u=Depends(sales_user), db=Depends(db_session)):
    s = student(db, sid)
    p = db.scalar(select(Plan).where(Plan.user_id == sid))
    result = {
        "student": public(s),
        "plan": payload(db, p) if p else None,
        "forecast": None,
        "actual": None,
        "guidance": [
            {"text": n.text, "created_at": n.created_at}
            for n in db.scalars(
                select(Note)
                .where(Note.student_id == sid, Note.internal == False)
                .order_by(Note.id.desc())
            )
        ],
        "notice": "Visão de leitura para preparar a consultoria. Projeção não comprova disponibilidade para contratar; avalie pendências, despesas e compromissos com o aluno. Não há score nem recomendação automática de crédito.",
    }
    if p:
        entries = list(db.scalars(select(Entry).where(Entry.plan_id == p.id)))
        result["forecast"] = calculate(p, entries, "forecast")
        result["actual"] = calculate(p, entries, "actual")
    audit(db, u, sid, "sales_financial_viewed")
    db.commit()
    return result


def appointment_write(db, data, u, existing=None):
    o = db.scalar(
        select(Opportunity)
        .where(Opportunity.id == data.opportunity_id)
        .with_for_update()
    )
    if not o:
        raise HTTPException(404, "Oportunidade não encontrada.")
    # The owner row lock serializes all bookings for this person, across different students.
    db.scalar(select(User).where(User.id == data.owner_id).with_for_update())
    owner(db, data.owner_id)
    end = data.starts_at + timedelta(minutes=data.duration_minutes)
    if data.status in ("agendada", "confirmada"):
        stmt = select(Appointment.id).where(
            Appointment.owner_id == data.owner_id,
            Appointment.status.in_(["agendada", "confirmada"]),
            Appointment.starts_at < end,
            Appointment.ends_at > data.starts_at,
        )
        if existing:
            stmt = stmt.where(Appointment.id != existing.id)
        if db.scalar(stmt):
            raise HTTPException(
                409,
                "O responsável já tem uma consultoria nesse horário. Escolha outro horário ou responsável.",
            )
    before = serialize_appointment(db, existing) if existing else None
    a = existing or Appointment()
    for key, value in data.model_dump(exclude={"version"}).items():
        setattr(a, key, value)
    a.ends_at = end
    if existing:
        a.version += 1
    else:
        db.add(a)
    if data.status in ("agendada", "confirmada") and o.stage == "aguardando":
        o.stage = "agendado"
        o.version += 1
        o.updated_at = now()
    elif data.status == "realizada" and o.stage in ("aguardando", "agendado"):
        o.stage = "consultoria"
        o.version += 1
        o.updated_at = now()
    db.flush()
    from fastapi.encoders import jsonable_encoder

    audit(
        db,
        u,
        o.student_id,
        "sales_appointment_updated" if existing else "sales_appointment_created",
        {
            "before": jsonable_encoder(before),
            "after": jsonable_encoder(serialize_appointment(db, a)),
        },
    )
    db.commit()
    return serialize_appointment(db, a)


@router.post("/appointments")
def create_appointment(
    data: AppointmentInput, u=Depends(sales_user), db=Depends(db_session)
):
    return appointment_write(db, data, u)


@router.put("/appointments/{aid}")
def edit_appointment(
    aid: int, data: AppointmentUpdate, u=Depends(sales_user), db=Depends(db_session)
):
    a = db.scalar(select(Appointment).where(Appointment.id == aid).with_for_update())
    if not a:
        raise HTTPException(404, "Reunião não encontrada.")
    if a.version != data.version:
        raise HTTPException(409, "Reunião alterada por outra pessoa. Reabra a agenda.")
    if a.opportunity_id != data.opportunity_id:
        raise HTTPException(422, "A reunião não pode ser transferida para outro aluno.")
    return appointment_write(db, data, u, a)


@router.get("/appointments")
def appointments(
    opportunity_id: int | None = None,
    owner_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    u=Depends(sales_user),
    db=Depends(db_session),
):
    stmt = select(Appointment)
    if opportunity_id:
        stmt = stmt.where(Appointment.opportunity_id == opportunity_id)
    if owner_id:
        stmt = stmt.where(Appointment.owner_id == owner_id)
    if from_date:
        stmt = stmt.where(
            Appointment.starts_at
            >= datetime.combine(
                from_date, time.min, ZoneInfo("America/Sao_Paulo")
            ).astimezone(timezone.utc)
        )
    if to_date:
        stmt = stmt.where(
            Appointment.starts_at
            < datetime.combine(
                to_date + timedelta(days=1), time.min, ZoneInfo("America/Sao_Paulo")
            ).astimezone(timezone.utc)
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    return {
        "items": [
            serialize_appointment(db, a)
            for a in db.scalars(
                stmt.order_by(Appointment.starts_at.desc(), Appointment.id.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
        ],
        "total": total,
        "page": page,
    }


@router.get("/analytics")
def analytics(
    from_date: date | None = None,
    to_date: date | None = None,
    u=Depends(sales_user),
    db=Depends(db_session),
):
    if from_date and to_date and from_date > to_date:
        raise HTTPException(422, "A data inicial deve ser anterior à final.")

    def period(stmt, col):
        if from_date:
            stmt = stmt.where(
                col
                >= datetime.combine(
                    from_date, time.min, ZoneInfo("America/Sao_Paulo")
                ).astimezone(timezone.utc)
            )
        if to_date:
            stmt = stmt.where(
                col
                < datetime.combine(
                    to_date + timedelta(days=1), time.min, ZoneInfo("America/Sao_Paulo")
                ).astimezone(timezone.utc)
            )
        return stmt

    student_count = db.scalar(
        select(func.count())
        .select_from(User)
        .where(cast(User.roles, String).like('%"aluno"%'))
    )
    stages = {s: 0 for s in STAGES}
    for stage, count in db.execute(
        period(
            select(Opportunity.stage, func.count()).group_by(Opportunity.stage),
            Opportunity.created_at,
        )
    ):
        stages[stage] = count
    scheduled = db.scalar(
        select(func.count(func.distinct(Opportunity.student_id)))
        .select_from(Appointment)
        .join(Opportunity, Opportunity.id == Appointment.opportunity_id)
        .where(
            Appointment.status.in_(["agendada", "confirmada"]),
            Appointment.starts_at >= now(),
        )
    )
    appointments_by_status = {
        s: 0
        for s in ["agendada", "confirmada", "realizada", "cancelada", "nao_compareceu"]
    }
    for status, count in db.execute(
        period(
            select(Appointment.status, func.count()).group_by(Appointment.status),
            Appointment.starts_at,
        )
    ):
        appointments_by_status[status] = count
    won = list(
        db.scalars(
            period(
                select(Opportunity).where(Opportunity.stage == "ganho"),
                Opportunity.closed_at,
            )
        )
    )
    value = sum(
        (
            (
                o.cash_price
                if o.selected_offer == "cash"
                else o.installment_value * o.installment_count
            )
            for o in won
        ),
        Decimal(0),
    )
    ranking = {}
    for o in won:
        key = o.owner_id
        if key not in ranking:
            responsible = db.get(User, key) if key else None
            ranking[key] = {
                "owner_id": key,
                "name": responsible.name if responsible else "Sem responsável",
                "sales": 0,
                "contract_value": Decimal(0),
            }
        ranking[key]["sales"] += 1
        ranking[key]["contract_value"] += (
            o.cash_price
            if o.selected_offer == "cash"
            else o.installment_value * o.installment_count
        )
    return {
        "students_registered": student_count,
        "students_scheduled": scheduled,
        "students_without_opportunity": max(
            0,
            student_count
            - db.scalar(
                select(func.count())
                .select_from(Opportunity)
                .join(User, User.id == Opportunity.student_id)
                .where(cast(User.roles, String).like('%"aluno"%'))
            ),
        ),
        "stages": stages,
        "appointments": appointments_by_status,
        "sales_count": len(won),
        "contract_value": str(value),
        "ranking": [
            {**v, "contract_value": str(v["contract_value"])} for v in ranking.values()
        ],
        "note": "Valores de contratos registrados, não recebimentos confirmados. Vendas pela data de fechamento; reuniões pela data agendada; funil pela data de entrada. Inscritos e próximos agendamentos são totais atuais.",
    }


@router.get("/export.csv")
def export(u=Depends(sales_user), db=Depends(db_session)):
    rows = list(db.scalars(select(Opportunity).order_by(Opportunity.id).limit(10001)))
    if len(rows) > 10000:
        raise HTTPException(
            422,
            "O relatório excede 10.000 registros. Solicite uma exportação filtrada à administração.",
        )

    def cell(value):
        s = "" if value is None else str(value)
        return "'" + s if s.startswith(("=", "+", "-", "@", "\t", "\r")) else s

    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(
        [
            "Aluno",
            "Celular",
            "Responsável",
            "Etapa",
            "À vista",
            "Parcelas",
            "Valor da parcela",
            "Total parcelado",
            "Condição aceita",
            "Valor do contrato",
            "Próximo contato",
        ]
    )
    for o in rows:
        d = serialize_op(db, o)
        writer.writerow(
            [
                cell(v)
                for v in [
                    d["student"]["name"],
                    d["student"]["phone"],
                    d["owner_name"],
                    STAGES[d["stage"]],
                    d["cash_price"],
                    d["installment_count"],
                    d["installment_value"],
                    d["installment_total"],
                    d["selected_offer"],
                    d["contract_total"],
                    str(d["next_contact"] or ""),
                ]
            ]
        )
    audit(db, u, None, "sales_export", {"count": len(rows)})
    db.commit()
    return StreamingResponse(
        iter(["\ufeff" + buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="comercial-p4.csv"'},
    )
