from copy import deepcopy
import pytest
from sqlalchemy import select
from fastapi.testclient import TestClient
from app.main import app
from app.db import SessionLocal
from app.models import User, Audit
from conftest import PASSWORD


def fields(c):
    u = c.get("/api/users?q=Pessoa%20fictícia%201").json()["items"][0]
    return {k: u[k] for k in ("name", "phone", "email")}


def test_admin_updates_profile_and_audit_without_financial_changes(login, payload):
    admin = login(5)
    student = login(1)
    original = fields(admin)
    plan = payload(student)
    with SessionLocal() as db:
        user = db.get(User, 1)
        before = (user.password_hash, user.status, user.expires_at, user.roles)
    response = admin.put(
        "/api/users/1/profile",
        json={
            **original,
            "name": "Nome atualizado",
            "email": "aluno@example.com",
            "original": original,
        },
    )
    assert response.status_code == 200, response.text
    assert student.get("/api/auth/me").json()["user"]["name"] == "Nome atualizado"
    assert payload(student) == plan
    with SessionLocal() as db:
        user = db.get(User, 1)
        assert before == (user.password_hash, user.status, user.expires_at, user.roles)
        a = db.scalar(select(Audit).where(Audit.action == "profile_changed"))
        assert a.actor == 5 and a.subject == 1 and a.details["before"] == original
        assert a.details["after"][
            "email"
        ] == "aluno@example.com" and "password" not in str(a.details)


@pytest.mark.parametrize("uid", [1, 3, 4, 6])
def test_profile_edit_is_admin_only(login, uid):
    c = login(uid)
    d = {"name": "Pessoa", "phone": "11987654321", "email": None}
    assert c.put("/api/users/1/profile", json={**d, "original": d}).status_code == 403


def test_profile_change_phone_normalization_and_invalidation(login):
    admin = login(5)
    student = login(1)
    original = fields(admin)
    grant = admin.post("/api/users/1/recovery").json()["token"]
    response = admin.put(
        "/api/users/1/profile",
        json={**original, "phone": "(11) 98765-4321", "original": original},
    )
    assert response.status_code == 200 and response.json()["phone"] == "+5511987654321"
    assert student.get("/api/auth/me").status_code == 401
    c = TestClient(app)
    assert (
        c.post(
            "/api/auth/login", json={"phone": original["phone"], "password": PASSWORD}
        ).status_code
        == 401
    )
    assert (
        c.post(
            "/api/auth/login", json={"phone": "11987654321", "password": PASSWORD}
        ).status_code
        == 200
    )
    assert (
        c.post(
            "/api/auth/reset", json={"token": grant, "password": "627491"}
        ).status_code
        == 400
    )


def test_profile_duplicate_does_not_partially_save(login):
    admin = login(5)
    original = fields(admin)
    with SessionLocal() as db:
        other = db.get(User, 2).phone
    response = admin.put(
        "/api/users/1/profile",
        json={**original, "name": "Não salvar", "phone": other, "original": original},
    )
    assert response.status_code == 409
    assert fields(admin) == original


def test_profile_stale_change_rejected(login):
    admin = login(5)
    original = fields(admin)
    first = {**original, "name": "Primeira edição", "original": original}
    assert admin.put("/api/users/1/profile", json=first).status_code == 200
    second = {**original, "name": "Edição desatualizada", "original": original}
    assert admin.put("/api/users/1/profile", json=second).status_code == 409
    with SessionLocal() as db:
        assert db.get(User, 1).name == "Primeira edição"


@pytest.mark.parametrize(
    "field,value",
    [("roles", ["administrador"]), ("password", "627491"), ("status", "ativo")],
)
def test_profile_cannot_change_permissions_or_password(login, field, value):
    admin = login(5)
    original = fields(admin)
    assert (
        admin.put(
            "/api/users/1/profile",
            json={**original, "original": original, field: value},
        ).status_code
        == 422
    )


def test_profile_unknown_student(login):
    admin = login(5)
    original = fields(admin)
    assert (
        admin.put(
            "/api/users/9999/profile", json={**original, "original": original}
        ).status_code
        == 404
    )


def test_demo_command_creates_once_without_overwriting(monkeypatch, capsys):
    from app.cli import main

    monkeypatch.setattr("sys.argv", ["cli", "demo"])
    monkeypatch.setenv("ALLOW_DEMO", "1")
    with SessionLocal() as db:
        for u in db.scalars(select(User)):
            u.phone = "+5511800000" + str(u.id).zfill(3)
        db.commit()
    main()
    capsys.readouterr()
    with SessionLocal() as db:
        first = list(db.scalars(select(User).order_by(User.id)))
        assert len(first) == 12
        hashes = {u.phone: u.password_hash for u in first}
    main()
    assert capsys.readouterr().out == ""
    with SessionLocal() as db:
        assert {u.phone: u.password_hash for u in db.scalars(select(User))} == hashes
