from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.db import SessionLocal
from app.models import User, Session, Entry, Audit, Reset
from app.security import now, annual, hash_password, check_password
from app.finance import months
from conftest import entry, PASSWORD


@pytest.mark.parametrize(
    "path",
    [
        "/api/plans/1",
        "/api/reports/1",
        "/api/reports/1/pdf",
        "/api/users",
        "/api/audit",
    ],
)
def test_unauthenticated(path):
    assert TestClient(app).get(path).status_code == 401


@pytest.mark.parametrize(
    "path", ["/api/plans/2", "/api/reports/2", "/api/reports/2/pdf", "/api/notes/2"]
)
def test_student_only_own(login, path):
    assert login(1).get(path).status_code == 403


@pytest.mark.parametrize("uid", [3, 5, 6, 7])
def test_financial_staff_all_students(login, uid):
    c = login(uid)
    assert c.get("/api/plans/1").status_code == 200
    assert c.get("/api/plans/2").status_code == 200
    assert c.get("/api/users").json()["total"] == 3


@pytest.mark.parametrize(
    "path",
    [
        "/api/plans/1",
        "/api/reports/1",
        "/api/reports/1/pdf",
        "/api/notes/1",
        "/api/audit?subject=1",
        "/api/audit",
        "/api/contents?all=true",
    ],
)
def test_seller_no_financial_access(login, path):
    assert login(4).get(path).status_code == 403


def test_seller_precadastro_no_activation(login):
    c = login(4)
    d = {"name": "Cadastro fictício", "phone": "+351912345678", "password": PASSWORD}
    r = c.post("/api/users", json=d)
    assert r.status_code == 201 and r.json()["status"] == "pendente"
    d["phone"] = "+351912345679"
    d["roles"] = ["administrador"]
    assert c.post("/api/users", json=d).status_code == 403
    assert c.post("/api/users/1/access", json={"action": "ativar"}).status_code == 403
    rows = c.get("/api/users").json()["items"]
    assert "password_hash" not in str(rows) and "entries" not in str(rows)


@pytest.mark.parametrize("uid", [1, 3, 4, 6])
def test_admin_only_access_roles(login, uid):
    c = login(uid)
    assert c.post("/api/users/2/access", json={"action": "renovar"}).status_code == 403
    assert (
        c.put("/api/users/2/roles", json={"roles": ["administrador"]}).status_code
        == 403
    )


@pytest.mark.parametrize("status", ["vencido", "bloqueado", "revogado", "pendente"])
def test_annual_access_with_open_session(login, status):
    c = login(1)
    assert c.get("/api/plans/1").status_code == 200
    with SessionLocal() as db:
        u = db.get(User, 1)
        if status == "vencido":
            u.expires_at = now() - timedelta(seconds=1)
        else:
            u.status = status
        db.commit()
    for path in [
        "/api/plans/1",
        "/api/reports/1",
        "/api/reports/1/pdf",
        "/api/notes/1",
        "/api/contents",
    ]:
        assert c.get(path).status_code == 403
    assert (
        c.get("/api/auth/me").status_code == 200
        and c.post("/api/renewals").status_code == 200
    )
    assert login(3).get("/api/plans/1").status_code == 200


def test_no_session_timeout_and_staff_no_annual_expiry(login):
    c = login(1)
    with SessionLocal() as db:
        s = db.scalar(select(Session).where(Session.user_id == 1))
        assert not hasattr(s, "expires_at")
        db.get(User, 3).expires_at = now() - timedelta(days=10)
        db.commit()
    assert c.get("/api/auth/me").status_code == 200
    assert login(3).get("/api/plans/1").status_code == 200


def test_leap_day():
    assert annual(datetime(2024, 2, 29, 15, tzinfo=timezone.utc)) == datetime(
        2025, 2, 28, 15, tzinfo=timezone.utc
    )


def test_renewal_idempotent_admin_approval_history(login):
    c = login(1)
    c.post("/api/renewals")
    c.post("/api/renewals")
    admin = login(5)
    assert len(admin.get("/api/renewals").json()) == 1
    assert (
        admin.post("/api/users/1/access", json={"action": "renovar"}).status_code == 200
    )
    assert admin.get("/api/renewals").json()[0]["status"] == "aprovada"
    assert len(c.get("/api/users/1/access-history").json()) == 1


def test_disable_staff_and_roles_invalidate_sessions(login):
    c = login(3)
    a = login(5)
    assert a.put("/api/users/3/enabled", json={"enabled": False}).status_code == 200
    assert c.get("/api/plans/1").status_code == 401
    assert a.put("/api/users/3/enabled", json={"enabled": True}).status_code == 200
    c = login(3)
    assert a.put("/api/users/3/roles", json={"roles": ["vendedor"]}).status_code == 200
    assert c.get("/api/auth/me").status_code == 401


def test_csrf_password_logout(login):
    c = login(1)
    csrf = c.headers.pop("X-CSRF-Token")
    assert c.post("/api/renewals").status_code == 403
    c.headers["X-CSRF-Token"] = csrf
    assert (
        c.post(
            "/api/auth/password",
            json={"old_password": PASSWORD, "password": "NovaSenhaSegura1234"},
        ).status_code
        == 200
    )
    assert c.get("/api/auth/me").status_code == 401
    c = login(2)
    assert c.post("/api/auth/logout").status_code == 200
    assert c.get("/api/auth/me").status_code == 401


def test_password_hash_reset_single_use(login):
    assert check_password(PASSWORD, hash_password(PASSWORD))
    a = login(5)
    token = a.post("/api/users/1/recovery").json()["token"]
    c = TestClient(app)
    d = {"token": token, "password": "NovaSenhaSegura1234"}
    assert c.post("/api/auth/reset", json=d).status_code == 200
    assert c.post("/api/auth/reset", json=d).status_code == 400
    with SessionLocal() as db:
        assert not list(db.scalars(select(Reset))) and PASSWORD not in str(
            [a.details for a in db.scalars(select(Audit))]
        )


def test_login_limit():
    c = TestClient(app)
    for _ in range(10):
        assert (
            c.post(
                "/api/auth/login",
                json={"phone": "+5511999990001", "password": "errada"},
            ).status_code
            == 401
        )
    assert (
        c.post(
            "/api/auth/login", json={"phone": "+5511999990001", "password": PASSWORD}
        ).status_code
        == 429
    )


def test_persistence_conflict_repeated_request(login, payload):
    c = login(1)
    p = payload(c)
    p["entries"] = [entry()]
    r = c.put("/api/plans/1", json=p)
    assert r.status_code == 200
    second = login(1)
    assert second.get("/api/plans/1").json()["entries"][0]["forecast"] == "1000.00"
    assert c.put("/api/plans/1", json=p).status_code == 409
    with SessionLocal() as db:
        assert len(list(db.scalars(select(Entry)))) == 1


def test_finance_payroll_card_actual_null(login, payload):
    c = login(1)
    p = payload(c)
    p["entries"] = [
        entry(value="2000.00", actual="1900.00"),
        entry("fixas", "500.00", actual="400.00"),
        entry("consignados", "300.00", deducted=True),
        entry("variaveis", "200.00", method="cartao"),
        entry("bancarias", "200.00", method="fatura"),
    ]
    assert c.put("/api/plans/1", json=p).status_code == 200
    r = c.get("/api/reports/1").json()["months"][0]
    assert (
        Decimal(r["outflow"]) == 700
        and Decimal(r["balance"]) == 1300
        and r["percentages"]["fixas"] == "25.00"
    )
    r = c.get("/api/reports/1?mode=actual").json()["months"][0]
    assert Decimal(r["outflow"]) == 400 and Decimal(r["balance"]) == 1500
    p = payload(c)
    p["card_mode"] = "fatura"
    p["entries"][0]["forecast"] = "0.00"
    p["entries"][2]["deducted"] = False
    assert c.put("/api/plans/1", json=p).status_code == 200
    r = c.get("/api/reports/1").json()["months"][0]
    assert Decimal(r["outflow"]) == 1000 and r["percentages"]["fixas"] is None
    p = payload(c)
    p["entries"][0]["forecast"] = None
    assert c.put("/api/plans/1", json=p).status_code == 200
    r = c.get("/api/reports/1").json()["months"][0]
    assert r["income"] is None and r["balance"] is None


def test_years_repetition_bounds_and_unknown_debt(login, payload):
    c = login(1)
    p = payload(c)
    assert months("2026-11")[-1] == "2027-10"
    p["entries"] = [entry("fixas", "100.00", month=m) for m in months(p["start"])[1:4]]
    p["debts"] = [
        {
            "key": "debt",
            "institution": "Banco fictício",
            "kind": "Empréstimo",
            "balance": None,
        }
    ]
    assert c.put("/api/plans/1", json=p).status_code == 200
    r = c.get("/api/reports/1").json()["months"]
    assert [Decimal(m["outflow"]) for m in r[:5]] == [0, 100, 100, 100, 0]
    assert c.get("/api/plans/1").json()["debts"][0]["balance"] is None
    p = payload(c)
    p["entries"].append(entry(month="2028-01"))
    assert c.put("/api/plans/1", json=p).status_code == 422


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-1", "1.001", "1e100"])
def test_money_validation(login, payload, value):
    c = login(1)
    p = payload(c)
    p["entries"] = [entry(value=value)]
    assert c.put("/api/plans/1", json=p).status_code == 422


def test_approved_spreadsheet_totals(login, payload):
    c = login(1)
    p = payload(c)
    p["completed"] = list(range(8))
    p["entries"] = [entry(value="1000.00", month=m) for m in months(p["start"])] + [
        entry("fixas", "20.00", label="Assinaturas"),
        entry("variaveis", "70.00"),
        entry("eventuais", "30.00"),
    ]
    assert c.put("/api/plans/1", json=p).status_code == 200
    r = c.get("/api/reports/1").json()
    assert (
        Decimal(r["totals"]["income"]) == 12000
        and Decimal(r["totals"]["outflow"]) == 120
        and Decimal(r["totals"]["balance"]) == 11880
    )
    assert Decimal(r["months"][0]["categories"]["eventuais"]) == 30


def test_internal_notes_pdf_shared_calculation(login, payload):
    staff = login(3)
    staff.post("/api/notes/1", json={"text": "INTERNO_CONFIDENCIAL", "internal": True})
    staff.post("/api/notes/1", json={"text": "Orientação pública", "internal": False})
    c = login(1)
    assert (
        len(c.get("/api/notes/1").json()) == 1
        and "INTERNO" not in c.get("/api/notes/1").text
    )
    p = payload(c)
    p["entries"] = [entry(value="1234.56")]
    assert c.put("/api/plans/1", json=p).status_code == 200
    r = c.get("/api/reports/1/pdf")
    assert r.status_code == 200 and r.content.startswith(b"%PDF")
    open("/tmp/p4-rebuild-report.pdf", "wb").write(r.content)


def test_content_publication_versions(login):
    a = login(5)
    s = login(1)
    d = {
        "title": "Renda",
        "text": "Texto revisado",
        "module": "Módulo 02",
        "lesson": "Aula 03",
        "reference": "p. 70",
        "context": "rendas",
        "status": "rascunho",
        "version": 1,
    }
    cid = a.post("/api/contents", json=d).json()["id"]
    assert s.get("/api/contents").json() == []
    d["status"] = "publicado"
    assert a.put(f"/api/contents/{cid}", json=d).status_code == 200
    assert len(s.get("/api/contents").json()) == 1
    assert len(a.get(f"/api/contents/{cid}/versions").json()) == 2
    assert a.put(f"/api/contents/{cid}", json=d).status_code == 409


def test_csv_preview_import_no_activation(login):
    a = login(5)
    d = {
        "text": "name,phone,email\nImportado fictício,+351912345678,aluno@example.com\n"
    }
    assert a.post("/api/import", json=d).json()["rows"][0]["valid"]
    assert a.post("/api/import", json={**d, "commit": True}).json()["committed"]
    assert not a.post("/api/import", json=d).json()["rows"][0]["valid"]
    assert a.get("/api/users?q=Importado").json()["items"][0]["status"] == "pendente"


def test_pagination_filters_and_delete_confirmation(login, payload):
    c = login(3)
    r = c.get("/api/users?completion=pendente&size=1").json()
    assert r["total"] == 3 and len(r["items"]) == 1
    assert c.get("/api/users?team=true").status_code == 403
    assert login(4).get("/api/users?completion=pendente").status_code == 403
    a = login(5)
    assert (
        a.request(
            "DELETE",
            "/api/users/1",
            json={"confirmation": "sim", "reason": "Solicitação fictícia validada"},
        ).status_code
        == 422
    )
    assert (
        a.request(
            "DELETE",
            "/api/users/1",
            json={
                "confirmation": "EXCLUIR +5511999990001",
                "reason": "Solicitação fictícia validada",
            },
        ).status_code
        == 200
    )
    with SessionLocal() as db:
        assert db.get(User, 1) is None
