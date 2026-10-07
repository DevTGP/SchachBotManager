from datetime import timedelta

from accounts import CSRF, PASSWORD
from stored_games import SITE

NEW_PASSWORD = "a long new password"


def create_link(admin, user_id):
    return admin.post(f"/api/v1/admin/users/{user_id}/password-reset", headers=CSRF)


def redeem(client, url, password=NEW_PASSWORD):
    token = url.split("#", 1)[1]
    body = {"token": token, "password": password}
    return client.post("/api/v1/password-resets/redeem", json=body, headers=CSRF)


def log_in(client, password):
    body = {"username": "coder", "password": password}
    return client.post("/api/v1/session", json=body, headers=CSRF)


def test_an_admin_link_sets_a_new_password_and_ends_old_sessions(app, admin, login):
    old_client, user = login()

    link = create_link(admin, user["_id"])
    assert link.status_code == 201
    assert link.json["url"].startswith(f"{SITE}/reset-password#")
    assert link.json["expires_at"] == "2026-05-02T12:00:00.000Z"

    fresh = app.test_client()
    response = redeem(fresh, link.json["url"])
    assert response.status_code == 200
    assert response.json["user"]["username"] == "coder"
    assert fresh.get("/api/v1/session").json["user"]["username"] == "coder"
    assert old_client.get("/api/v1/session").json == {"user": None}

    assert log_in(app.test_client(), PASSWORD).status_code == 401
    assert log_in(app.test_client(), NEW_PASSWORD).status_code == 200


def test_a_link_works_once_and_a_new_one_replaces_it(app, admin, login):
    _, user = login()
    first = create_link(admin, user["_id"]).json["url"]
    second = create_link(admin, user["_id"]).json["url"]

    assert redeem(app.test_client(), first).json["code"] == "invalid_token"
    assert redeem(app.test_client(), second).status_code == 200
    assert redeem(app.test_client(), second).json["code"] == "invalid_token"


def test_a_link_expires_after_a_day(app, admin, login, clock):
    _, user = login()
    url = create_link(admin, user["_id"]).json["url"]

    clock.advance(timedelta(hours=24))

    assert redeem(app.test_client(), url).status_code == 400


def test_the_new_password_must_be_long_enough(app, admin, login):
    _, user = login()
    url = create_link(admin, user["_id"]).json["url"]

    response = redeem(app.test_client(), url, "short")

    assert response.status_code == 400
    assert response.json["field"] == "password"
    assert redeem(app.test_client(), url).status_code == 200


def test_unknown_accounts_get_no_link(admin):
    response = create_link(admin, "0123456789abcdef01234567")
    assert response.status_code == 404
