import os, secrets, hashlib, hmac
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from fastapi import Request, Depends, HTTPException
from sqlalchemy import delete
from .db import db_session
from .models import User, Session, Audit

COOKIE = "p4_session"
PRODUCTION = os.getenv("APP_ENV") == "production"


def now():
    return datetime.now(timezone.utc)


def aware(v):
    return v.replace(tzinfo=timezone.utc) if v and v.tzinfo is None else v


def digest(s):
    return hashlib.sha256(s.encode()).hexdigest()


def hash_password(s):
    if not 12 <= len(s) <= 200:
        raise ValueError("Use uma senha de 12 a 200 caracteres.")
    salt = secrets.token_hex(16)
    return (
        salt
        + "$"
        + hashlib.scrypt(s.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
    )


def check_password(s, stored):
    try:
        salt, hashed = stored.split("$")
        return hmac.compare_digest(
            hashlib.scrypt(
                s.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1
            ).hex(),
            hashed,
        )
    except (ValueError, TypeError):
        return False


DUMMY = hash_password(secrets.token_urlsafe(24))


def annual(start):
    local = aware(start).astimezone(ZoneInfo("America/Sao_Paulo"))
    try:
        end = local.replace(year=local.year + 1)
    except ValueError:
        end = local.replace(year=local.year + 1, day=28)
    return end.astimezone(timezone.utc)


def status(u):
    return (
        "vencido"
        if u.status == "ativo" and (not u.expires_at or aware(u.expires_at) <= now())
        else u.status
    )


def public(u):
    return {
        "id": u.id,
        "name": u.name,
        "phone": u.phone,
        "email": u.email,
        "roles": u.roles,
        "enabled": u.enabled,
        "status": status(u),
        "released_at": u.released_at,
        "expires_at": u.expires_at,
    }


def require(u, *roles):
    if not set(u.roles) & set(roles):
        raise HTTPException(403, "Seu perfil não permite esta operação.")


def current(request: Request, db=Depends(db_session)):
    token = request.cookies.get(COOKIE, "")
    s = db.get(Session, digest(token)) if token else None
    if not s:
        raise HTTPException(401, "Entre para continuar.")
    u = db.get(User, s.user_id)
    if not u or not u.enabled:
        raise HTTPException(401, "Conta indisponível. Consulte a equipe.")
    if request.method not in ("GET", "HEAD", "OPTIONS") and not hmac.compare_digest(
        request.headers.get("X-CSRF-Token", ""), s.csrf
    ):
        raise HTTPException(403, "Atualize a página para renovar a proteção da sessão.")
    request.state.session = s
    return u


def financial(db, u, sid):
    target = db.get(User, sid)
    if not target or "aluno" not in target.roles:
        raise HTTPException(404, "Aluno não encontrado.")
    if set(u.roles) & {"consultor", "administrador"}:
        return target
    if u.id != sid or "aluno" not in u.roles:
        raise HTTPException(403, "Você não tem acesso a estes dados.")
    if status(u) != "ativo":
        raise HTTPException(
            403,
            "Seu acesso financeiro está "
            + status(u)
            + ". Consulte sua conta para solicitar renovação.",
        )
    return target


def audit(db, u, sid, action, details=None):
    db.add(
        Audit(
            actor=u.id if u else None, subject=sid, action=action, details=details or {}
        )
    )


def invalidate(db, uid):
    db.execute(delete(Session).where(Session.user_id == uid))
