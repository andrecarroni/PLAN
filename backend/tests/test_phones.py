import pytest
from app.phones import normalize_phone
from app.schemas import UserInput, Login


@pytest.mark.parametrize(
    "value,expected",
    [
        ("11987654321", "+5511987654321"),
        ("(11) 98765-4321", "+5511987654321"),
        ("1134567890", "+551134567890"),
        ("5511987654321", "+5511987654321"),
        ("+55 (11) 98765-4321", "+5511987654321"),
        ("+351912345678", "+351912345678"),
        ("+1 (202) 555-0198", "+12025550198"),
        ("55987654321", "+5555987654321"),
    ],
)
def test_country_normalization(value, expected):
    assert normalize_phone(value) == expected
    assert (
        UserInput(name="Pessoa fictícia", phone=value, password="627491").phone
        == expected
    )
    assert Login(phone=value, password="627491").phone == expected


@pytest.mark.parametrize("value", ["123", "+55", "abc11987654321", "351912345678"])
def test_invalid_phone_keeps_international_rules(value):
    with pytest.raises(ValueError):
        normalize_phone(value)


def test_national_registration_login_and_duplicate_country(login):
    admin = login(5)
    result = admin.post(
        "/api/users",
        json={
            "name": "Pessoa fictícia",
            "phone": "(11) 98765-4321",
            "password": "627491",
        },
    )
    assert result.status_code == 201 and result.json()["phone"] == "+5511987654321"
    duplicate = admin.post(
        "/api/users",
        json={
            "name": "Outra pessoa fictícia",
            "phone": "+5511987654321",
            "password": "627491",
        },
    )
    assert duplicate.status_code == 409
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    assert (
        client.post(
            "/api/auth/login", json={"phone": "11987654321", "password": "627491"}
        ).status_code
        == 200
    )


def test_csv_duplicate_after_country_normalization(login):
    admin = login(5)
    result = admin.post(
        "/api/import",
        json={
            "text": "name,phone\nPessoa fictícia,11987654321\nOutra fictícia,+5511987654321\n"
        },
    )
    rows = result.json()["rows"]
    assert rows[0]["valid"] and not rows[1]["valid"]
