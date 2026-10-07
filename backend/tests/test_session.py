from datetime import timedelta

from flask.testing import FlaskClient
from sbm_store import users
from sbm_store.names import RATE_LIMITS, SESSIONS

from sbm_api.app import create_app

from accounts import CSRF, PASSWORD, add_user
from stored_games import SITE


def log_in(client, username="alice", password=PASSWORD):
    return client.post(
        "/api/v1/session", json={"username": username, "password": password}, headers=CSRF
    )


def test_a_guest_has_no_user(client):
    response = client.get("/api/v1/session")
    assert response.status_code == 200
    assert response.json == {"user": None}


def test_login_sets_a_protected_cookie(client, db):
    user, _ = add_user(db, "alice")

    response = log_in(client)

    assert response.status_code == 200
    assert response.json == {"user": {"id": str(user["_id"]), "username": "alice", "role": "coder"}}
    cookie = response.headers["Set-Cookie"]
    for attribute in ("HttpOnly", "SameSite=Strict", "Path=/api/", "Secure", "Max-Age=1209600"):
        assert attribute in cookie
    assert client.get("/api/v1/session").json["user"]["username"] == "alice"
    assert users.get(db, user["_id"])["last_login_at"] is not None


def test_the_name_is_case_insensitive(client, db):
    add_user(db, "Alice")

    assert log_in(client, "aLICE").json["user"]["username"] == "Alice"


def test_wrong_password_unknown_name_and_deactivated_look_the_same(client, db):
    add_user(db, "alice")
    add_user(db, "bob", active=False)

    for username, password in (
        ("alice", "wrong password"),
        ("nobody", PASSWORD),
        ("bob", PASSWORD),
    ):
        response = log_in(client, username, password)
        assert response.status_code == 401
        assert response.json["code"] == "invalid_credentials"
    assert client.get("/api/v1/session").json == {"user": None}


def test_logout_ends_the_session(client, db):
    add_user(db, "alice")
    log_in(client)

    response = client.delete("/api/v1/session", headers=CSRF)

    assert response.status_code == 204
    assert client.get("/api/v1/session").json == {"user": None}
    assert db[SESSIONS].count_documents({}) == 0


def test_logout_without_a_session_is_fine(client):
    assert client.delete("/api/v1/session", headers=CSRF).status_code == 204


def test_requests_other_than_get_need_the_csrf_header(client, db):
    add_user(db, "alice")

    response = client.post("/api/v1/session", json={"username": "alice", "password": PASSWORD})

    assert response.status_code == 403
    assert response.json["code"] == "csrf_failed"


def test_invalid_bodies_are_rejected(client):
    for body in ([], {"username": "alice"}, {"username": "a", "password": "b", "extra": 1}):
        response = client.post("/api/v1/session", json=body, headers=CSRF)
        assert response.status_code == 400
        assert response.json["code"] == "invalid_parameter"


def test_five_wrong_passwords_lock_the_account(client, db, clock):
    add_user(db, "alice")
    for _ in range(5):
        assert log_in(client, password="wrong password").status_code == 401

    locked = log_in(client)
    assert locked.status_code == 429
    assert locked.json["code"] == "too_many_attempts"
    assert locked.headers["Retry-After"] == "900"

    clock.advance(timedelta(minutes=15))
    assert log_in(client).status_code == 200


def test_too_many_attempts_from_one_address(client, db):
    add_user(db, "alice")
    for _ in range(30):
        log_in(client, "nobody")

    response = log_in(client)

    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) >= 1


def test_a_deactivated_account_loses_its_session(client, db):
    user, _ = add_user(db, "alice")
    log_in(client)

    users.update(db, user["_id"], {"active": False})

    assert client.get("/api/v1/session").json == {"user": None}


def test_an_expired_session_is_gone(client, db, clock):
    add_user(db, "alice")
    log_in(client)

    clock.advance(timedelta(days=14))

    assert client.get("/api/v1/session").json == {"user": None}


def test_a_used_session_is_extended_once_a_day(client, db, clock):
    add_user(db, "alice")
    log_in(client)
    start = clock.now()

    clock.advance(timedelta(hours=12))
    assert "Set-Cookie" not in client.get("/api/v1/session").headers

    clock.advance(timedelta(hours=13))
    response = client.get("/api/v1/session")
    assert "Max-Age=1209600" in response.headers["Set-Cookie"]
    session = db[SESSIONS].find_one()
    assert session["expires_at"] == start + timedelta(days=14, hours=25)

    clock.advance(timedelta(days=13))
    assert client.get("/api/v1/session").json["user"] is not None


def test_proxies_in_front_give_the_client_address(db, clock):
    app = create_app(db, now=clock.now, public_url=SITE, proxy_hops=2)
    client = app.test_client()
    forwarded = {"X-Forwarded-For": "203.0.113.7, 10.0.0.2"} | CSRF

    client.post("/api/v1/session", json={"username": "a", "password": "b"}, headers=forwarded)

    assert db[RATE_LIMITS].find_one()["_id"].startswith("auth:203.0.113.7:")


def test_unknown_paths_stay_not_found_without_the_csrf_header(app):
    # The plain client: the OpenAPI document does not know these paths.
    client = FlaskClient(app, app.response_class)

    assert client.post("/api/v1/nowhere").status_code == 404
    assert client.put("/api/v1/session").status_code == 405
