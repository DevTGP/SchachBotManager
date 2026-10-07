from sbm_store.names import AUDIT_LOG

from accounts import CSRF
from stored_games import SITE


def create(admin, **body):
    return admin.post("/api/v1/admin/invites", json={"role": "coder"} | body, headers=CSRF)


def test_create_an_invite_with_a_one_time_link(admin, db):
    response = create(admin)

    assert response.status_code == 201
    invite = response.json["invite"]
    assert invite["role"] == "coder"
    assert invite["created_by"] == "admin"
    assert invite["expires_at"] == "2026-05-08T12:00:00.000Z"
    assert response.json["url"].startswith(f"{SITE}/invite#")
    token = response.json["url"].split("#", 1)[1]
    assert token not in str(list(db.invites.find()))
    assert db[AUDIT_LOG].find_one({"action": "invite.create"})["target"] is not None


def test_the_link_creates_an_account(admin, app):
    url = create(admin, role="admin", valid_days=1).json["url"]
    body = {"token": url.split("#", 1)[1], "username": "carol", "password": "a long password"}

    response = app.test_client().post("/api/v1/invites/redeem", json=body, headers=CSRF)

    assert response.json["user"]["role"] == "admin"
    assert admin.get("/api/v1/admin/invites").json == {"items": []}


def test_list_and_revoke_open_invites(admin):
    first = create(admin).json["invite"]
    second = create(admin, valid_days=30).json["invite"]

    assert admin.get("/api/v1/admin/invites").json["items"] == [second, first]

    assert admin.delete(f"/api/v1/admin/invites/{first['id']}", headers=CSRF).status_code == 204
    assert admin.get("/api/v1/admin/invites").json["items"] == [second]
    assert admin.delete(f"/api/v1/admin/invites/{first['id']}", headers=CSRF).status_code == 404


def test_invalid_invites(admin):
    for body, field in (({"role": "king"}, "role"), ({"valid_days": 31}, "valid_days")):
        response = create(admin, **body)
        assert response.status_code == 400
        assert response.json["field"] == field
