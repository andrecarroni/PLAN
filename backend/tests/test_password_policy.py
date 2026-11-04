import pytest
from pydantic import ValidationError
from sqlalchemy import select
from app.db import SessionLocal
from app.models import User
from app.security import hash_password, check_password
from app.schemas import UserInput, Password, ResetInput
from conftest import PASSWORD


@pytest.mark.parametrize(
    "length,valid", [(5, False), (6, True), (200, True), (201, False)]
)
def test_password_length_boundaries(length, valid):
    value = "7" * length
    factories = [
        lambda: hash_password(value),
        lambda: UserInput(
            name="Pessoa fictícia", phone="+351912345678", password=value
        ),
        lambda: Password(old_password=PASSWORD, password=value),
        lambda: ResetInput(token="fictitious", password=value),
    ]
    for factory in factories:
        if valid:
            factory()
        else:
            with pytest.raises(ValueError):
                factory()


def test_six_digit_password_create_login_change_and_recover(login):
    admin = login(5)
    created = admin.post(
        "/api/users",
        json={
            "name": "Pessoa fictícia",
            "phone": "+351912345678",
            "password": "627491",
        },
    )
    assert created.status_code == 201, created.text
    uid = created.json()["id"]
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    result = client.post(
        "/api/auth/login", json={"phone": "+351912345678", "password": "627491"}
    )
    assert result.status_code == 200
    client.headers["X-CSRF-Token"] = result.json()["csrf"]
    assert (
        client.post(
            "/api/auth/password", json={"old_password": "627491", "password": "845291"}
        ).status_code
        == 200
    )
    token = admin.post(f"/api/users/{uid}/recovery").json()["token"]
    assert (
        client.post(
            "/api/auth/reset", json={"token": token, "password": "592847"}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/auth/login", json={"phone": "+351912345678", "password": "592847"}
        ).status_code
        == 200
    )
    with SessionLocal() as db:
        stored = db.get(User, uid).password_hash
        assert stored != "592847" and check_password("592847", stored)


def test_admin_cli_six_digits_and_safe_validation(monkeypatch, capsys):
    from app.cli import main

    monkeypatch.setattr("sys.argv", ["cli", "create-admin"])
    answers = iter(["Administrador fictício", "(11) 98765-4321"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    monkeypatch.setattr("getpass.getpass", lambda _: "627491")
    main()
    assert "Administrador criado." in capsys.readouterr().out
    with SessionLocal() as db:
        assert db.scalar(select(User).where(User.phone == "+5511987654321")) is not None
    answers = iter(["Administrador fictício", "123"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert "código do país" in str(exc.value) and "627491" not in str(exc.value)
