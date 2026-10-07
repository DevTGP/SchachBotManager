from sbm_store.names import AUDIT_LOG

from accounts import CSRF, add_user


def test_lists_accounts_by_name(admin, db):
    add_user(db, "Zoe")
    add_user(db, "bob", active=False)

    response = admin.get("/api/v1/admin/users")

    assert response.status_code == 200
    items = response.json["items"]
    assert [user["username"] for user in items] == ["admin", "bob", "Zoe"]
    assert items[0]["last_login_at"] == "2026-05-01T12:00:00.000Z"
    assert items[1] == {
        "id": items[1]["id"],
        "username": "bob",
        "role": "coder",
        "active": False,
        "created_at": "2026-05-01T12:00:00.000Z",
        "last_login_at": None,
    }


def test_change_the_role_and_record_it(admin, db, login):
    coder, user = login()

    response = admin.patch(
        f"/api/v1/admin/users/{user['_id']}", json={"role": "admin"}, headers=CSRF
    )

    assert response.status_code == 200
    assert response.json["role"] == "admin"
    assert coder.get("/api/v1/admin/users").status_code == 200
    entry = db[AUDIT_LOG].find_one({"action": "user.update"})
    assert (entry["actor"], entry["target"], entry["details"]) == (
        "admin",
        user["_id"],
        {"role": "admin"},
    )


def test_deactivating_ends_the_sessions(admin, login):
    coder, user = login()

    response = admin.patch(
        f"/api/v1/admin/users/{user['_id']}", json={"active": False}, headers=CSRF
    )

    assert response.json["active"] is False
    assert coder.get("/api/v1/session").json == {"user": None}


def test_admins_cannot_change_themselves(admin):
    me = admin.get("/api/v1/session").json["user"]["id"]

    response = admin.patch(f"/api/v1/admin/users/{me}", json={"role": "coder"}, headers=CSRF)

    assert response.status_code == 400
    assert response.json["field"] == "user_id"


def test_invalid_changes(admin, login):
    _, user = login()
    path = f"/api/v1/admin/users/{user['_id']}"

    for body, field in (({}, "body"), ({"role": "king"}, "role"), ({"active": "no"}, "active")):
        response = admin.patch(path, json=body, headers=CSRF)
        assert response.status_code == 400
        assert response.json["field"] == field
    assert (
        admin.patch("/api/v1/admin/users/nope", json={"active": True}, headers=CSRF).status_code
        == 400
    )
    missing = admin.patch(
        "/api/v1/admin/users/0123456789abcdef01234567", json={"active": True}, headers=CSRF
    )
    assert missing.status_code == 404
