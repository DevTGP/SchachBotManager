"""POST and PATCH /admin/disciplines (E100)."""

from datetime import timedelta

import pytest
from bson import ObjectId
from sbm_store.names import AUDIT_LOG

from accounts import CSRF


def create(client, **body):
    request = {"name": "Blitz", "initial_time_ms": 180_000} | body
    return client.post("/api/v1/admin/disciplines", json=request, headers=CSRF)


def update(client, discipline_id: str, **body):
    return client.patch(f"/api/v1/admin/disciplines/{discipline_id}", json=body, headers=CSRF)


def test_create_with_defaults_and_record_it(admin, db):
    response = create(admin, name="  Blitz  ", increment_ms=2000)

    assert response.status_code == 201
    assert response.json == {
        "id": response.json["id"],
        "name": "Blitz",
        "initial_time_ms": 180_000,
        "increment_ms": 2000,
        "startup_ms": 10_000,
        "tolerance_ms": 20,
        "max_moves": 500,
        "archived": False,
        "created_at": "2026-05-01T12:00:00.000Z",
        "updated_at": "2026-05-01T12:00:00.000Z",
    }
    entry = db[AUDIT_LOG].find_one({"action": "discipline.create"})
    assert (entry["actor"], entry["target"], entry["details"]) == (
        "admin",
        ObjectId(response.json["id"]),
        {"name": "Blitz"},
    )


def test_names_are_unique_regardless_of_case(admin):
    create(admin)

    response = create(admin, name="BLITZ")

    assert response.status_code == 409
    assert (response.json["code"], response.json["field"]) == ("name_taken", "name")


@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({"name": ""}, "name"),
        ({"name": "   "}, "name"),
        ({"name": "x" * 41}, "name"),
        ({"name": "a\tb"}, "name"),
        ({"initial_time_ms": 999}, "initial_time_ms"),
        ({"increment_ms": -1}, "increment_ms"),
        ({"startup_ms": 60_001}, "startup_ms"),
        ({"tolerance_ms": 1001}, "tolerance_ms"),
        ({"max_moves": 0}, "max_moves"),
        ({"archived": True}, "archived"),
    ],
)
def test_invalid_settings(admin, db, body, field):
    response = create(admin, **body)

    assert (response.status_code, response.json["field"]) == (400, field)
    assert db.disciplines.count_documents({}) == 0


def test_change_and_archive(admin, client, clock, db):
    discipline_id = create(admin).json["id"]
    clock.advance(timedelta(minutes=5))

    response = update(admin, discipline_id, name="Blitz 3+2", increment_ms=2000, archived=True)

    assert response.status_code == 200
    assert (response.json["name"], response.json["increment_ms"]) == ("Blitz 3+2", 2000)
    assert response.json["archived"] is True
    assert response.json["updated_at"] == "2026-05-01T12:05:00.000Z"
    entry = db[AUDIT_LOG].find_one({"action": "discipline.update"})
    assert entry["details"] == {"name": "Blitz 3+2", "increment_ms": 2000, "archived": True}
    listed = client.get("/api/v1/disciplines").json["items"]
    assert [item["name"] for item in listed] == ["Blitz 3+2"]


def test_a_rename_may_not_take_another_name(admin):
    create(admin)
    rapid = create(admin, name="Rapid", initial_time_ms=600_000).json["id"]

    response = update(admin, rapid, name="blitz")

    assert (response.status_code, response.json["code"]) == (409, "name_taken")


def test_invalid_changes(admin):
    discipline_id = create(admin).json["id"]

    assert update(admin, discipline_id).json["field"] == "body"
    assert update(admin, discipline_id, archived="yes").json["field"] == "archived"
    assert update(admin, discipline_id, colour="white").status_code == 400
    assert update(admin, "0123456789abcdef01234567", name="x").status_code == 404
    assert update(admin, "nope", name="x").json["field"] == "discipline_id"


def test_only_for_admins(login, client):
    coder, _ = login()

    assert create(coder).status_code == 403
    assert create(client).status_code == 401
    assert update(coder, "0123456789abcdef01234567", name="x").status_code == 403
