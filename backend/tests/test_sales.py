from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from sqlalchemy import select
from app.db import SessionLocal
from app.models import User, Opportunity, Appointment, Audit, Content
from conftest import PASSWORD, entry


def new(c, sid=1, owner=4):
    r = c.post("/api/sales/opportunities", json={"student_id": sid, "owner_id": owner})
    assert r.status_code == 200, r.text
    return r.json()


def body(o, **changes):
    d = {
        k: o[k]
        for k in [
            "version",
            "owner_id",
            "stage",
            "cash_price",
            "installment_count",
            "installment_value",
            "selected_offer",
            "next_contact",
            "notes",
            "lost_reason",
        ]
    }
    return {**d, **changes}


def booking(o, **changes):
    return {
        "opportunity_id": o["id"],
        "owner_id": 4,
        "starts_at": "2027-01-10T12:00:00-03:00",
        "duration_minutes": 45,
        "status": "agendada",
        "meeting_url": "https://meet.example.com/fictitious",
        "notes": "Teste fictício",
        **changes,
    }


@pytest.mark.parametrize("uid", [1, 2, 3, 7])
@pytest.mark.parametrize(
    "path",
    [
        "/api/sales/analytics",
        "/api/sales/opportunities",
        "/api/sales/appointments",
        "/api/sales/financial/1",
        "/api/sales/export.csv",
    ],
)
def test_commercial_permissions(login, uid, path):
    assert login(uid).get(path).status_code == 403


def test_sales_queue_idempotent_and_separated_from_staff(login):
    c = login(4)
    assert (
        c.post("/api/sales/queue/sync", json={"confirm": True}).json()["created"] == 3
    )
    assert (
        c.post("/api/sales/queue/sync", json={"confirm": True}).json()["created"] == 0
    )
    rows = c.get("/api/sales/opportunities").json()
    assert rows["total"] == 3
    assert new(c)["id"] in [x["id"] for x in rows["items"]]
    with SessionLocal() as db:
        assert len(list(db.scalars(select(Opportunity)))) == 3
        assert db.get(User, 1).roles == ["aluno"] and db.get(User, 4).roles == [
            "vendedor"
        ]
    stats = c.get("/api/sales/analytics").json()
    assert (
        stats["students_registered"] == 3 and stats["students_without_opportunity"] == 0
    )


def test_seller_financial_snapshot_is_read_only_and_audited(login, payload):
    student = login(1)
    p = payload(student)
    p["entries"] = [entry(value="3000.00"), entry("fixas", "1000.00")]
    assert student.put("/api/plans/1", json=p).status_code == 200
    staff = login(3)
    staff.post("/api/notes/1", json={"text": "INTERNO_NAO_COMERCIAL", "internal": True})
    staff.post("/api/notes/1", json={"text": "Orientação publicada", "internal": False})
    seller = login(4)
    r = seller.get("/api/sales/financial/1")
    assert r.status_code == 200
    data = r.json()
    assert Decimal(data["forecast"]["months"][0]["balance"]) == 2000
    assert (
        "INTERNO_NAO_COMERCIAL" not in r.text
        and data["guidance"][0]["text"] == "Orientação publicada"
    )
    assert seller.put("/api/plans/1", json=p).status_code == 403
    assert seller.get("/api/plans/1").status_code == 403
    with SessionLocal() as db:
        assert (
            db.scalar(
                select(Audit).where(Audit.action == "sales_financial_viewed")
            ).actor
            == 4
        )
    assert seller.get("/api/sales/financial/2").json()["plan"] is None


def test_sales_proposal_closure_and_nominal_value(login):
    c = login(4)
    o = new(c)
    assert o["cash_price"] == "5000.00" and o["installment_total"] == "5964.00"
    assert (
        c.put(
            "/api/sales/opportunities/" + str(o["id"]), json=body(o, stage="ganho")
        ).status_code
        == 422
    )
    r = c.put(
        "/api/sales/opportunities/" + str(o["id"]),
        json=body(
            o,
            stage="ganho",
            selected_offer="installments",
            notes="Proposta aceita em teste",
        ),
    )
    assert r.status_code == 200, r.text
    assert r.json()["contract_total"] == "5964.00" and r.json()["closed_at"]
    stats = c.get("/api/sales/analytics").json()
    assert stats["sales_count"] == 1 and Decimal(stats["contract_value"]) == 5964
    assert (
        c.put(
            "/api/sales/opportunities/" + str(o["id"]), json=body(o, stage="negociacao")
        ).status_code
        == 409
    )
    with SessionLocal() as db:
        assert (
            db.get(User, 1).status == "ativo"
        )  # Closing a sale does not manage annual access.


def test_appointments_duration_conflict_reschedule_and_stage(login):
    c = login(4)
    o = new(c)
    second = new(c, 2)
    r = c.post("/api/sales/appointments", json=booking(o))
    assert r.status_code == 200, r.text
    a = r.json()
    assert a["duration_minutes"] == 45
    assert (
        c.get("/api/sales/opportunities/" + str(o["id"])).json()["stage"] == "agendado"
    )
    assert (
        c.post(
            "/api/sales/appointments",
            json=booking(second, starts_at="2027-01-10T12:30:00-03:00"),
        ).status_code
        == 409
    )
    assert (
        c.post(
            "/api/sales/appointments",
            json=booking(second, starts_at="2027-01-10T12:45:00-03:00"),
        ).status_code
        == 200
    )
    data = {
        **booking(o, starts_at="2027-01-10T13:30:00-03:00"),
        "version": a["version"],
    }
    r = c.put("/api/sales/appointments/" + str(a["id"]), json=data)
    assert r.status_code == 200
    assert (
        c.put("/api/sales/appointments/" + str(a["id"]), json=data).status_code == 409
    )
    data = {**data, "version": r.json()["version"], "status": "realizada"}
    assert (
        c.put("/api/sales/appointments/" + str(a["id"]), json=data).status_code == 200
    )
    assert (
        c.get("/api/sales/opportunities/" + str(o["id"])).json()["stage"]
        == "consultoria"
    )
    assert c.get("/api/sales/analytics").json()["appointments"]["realizada"] == 1


def test_appointment_owner_and_timezone_validation(login):
    c = login(4)
    o = new(c)
    assert (
        c.post("/api/sales/appointments", json=booking(o, owner_id=3)).status_code
        == 422
    )
    assert (
        c.post(
            "/api/sales/appointments", json=booking(o, starts_at="2027-01-10T12:00:00")
        ).status_code
        == 422
    )
    assert (
        c.post(
            "/api/sales/appointments",
            json=booking(o, meeting_url="javascript:alert(1)"),
        ).status_code
        == 422
    )
    assert (
        c.put(
            "/api/sales/opportunities/" + str(o["id"]), json=body(o, owner_id=3)
        ).status_code
        == 422
    )


def test_sales_export_guard_and_date_filters(login):
    c = login(4)
    o = new(c)
    with SessionLocal() as db:
        db.get(User, 1).name = "=FICTITIOUS()"
        db.commit()
    r = c.get("/api/sales/export.csv")
    assert r.status_code == 200 and "'=FICTITIOUS()" in r.text and "'+55" in r.text
    assert (
        c.get(
            "/api/sales/analytics?from_date=2027-02-01&to_date=2027-01-01"
        ).status_code
        == 422
    )
    assert c.get("/api/sales/opportunities?size=1").json()["total"] == 1


def test_staff_registration_and_edit_separated_from_students(login):
    a = login(5)
    team = a.get("/api/users?team=true").json()
    assert team["total"] == 5 and all(
        set(x["roles"]) & {"vendedor", "consultor", "administrador"}
        for x in team["items"]
    )
    assert a.get("/api/users").json()["total"] == 3
    data = {
        "name": "Equipe fictícia",
        "phone": "11987654321",
        "password": "627491",
        "roles": ["consultor", "vendedor"],
    }
    assert a.post("/api/users", json=data).status_code == 422
    r = a.post("/api/team", json=data)
    assert r.status_code == 201, r.text
    staff = r.json()
    assert staff["phone"] == "+5511987654321" and "aluno" not in staff["roles"]
    original = {k: staff[k] for k in ["name", "phone", "email"]}
    assert (
        a.put(
            "/api/users/" + str(staff["id"]) + "/profile",
            json={**original, "name": "Nome da equipe revisado", "original": original},
        ).status_code
        == 404
    )
    r = a.put(
        "/api/users/" + str(staff["id"]) + "/profile?team=true",
        json={**original, "name": "Nome da equipe revisado", "original": original},
    )
    assert r.status_code == 200
    assert login(4).post("/api/team", json=data).status_code == 403
    assert (
        a.post(
            "/api/team", json={**data, "phone": "11987654322", "roles": ["aluno"]}
        ).status_code
        == 422
    )


def test_published_course_available_to_sales_but_not_drafts(login):
    with SessionLocal() as db:
        db.add(
            Content(
                title="Aula revisada",
                text="Texto publicado",
                module="Módulo",
                lesson="Aula",
                reference="página",
                context="rendas",
                status="publicado",
            )
        )
        db.add(
            Content(
                title="Rascunho",
                text="Texto privado",
                module="Módulo",
                lesson="Aula",
                reference="página",
                context="rendas",
                status="rascunho",
            )
        )
        db.commit()
    c = login(4)
    rows = c.get("/api/contents").json()
    assert len(rows) == 1 and rows[0]["title"] == "Aula revisada"
    assert c.get("/api/contents?all=true").status_code == 403
