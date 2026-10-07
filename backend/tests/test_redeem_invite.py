from datetime import timedelta

from sbm_store import invites, users
from sbm_store.names import INVITES

from accounts import CSRF, add_user
from stored_games import NOW

NEW_PASSWORD = "a long new password"


def new_invite(db, role=users.CODER, valid=timedelta(days=7)):
    _, token = invites.create(
        db, role, created_by=None, created_by_name=None, now=NOW, expires_at=NOW + valid
    )
    return token


def redeem(client, token, username="carol", password=NEW_PASSWORD):
    body = {"token": token, "username": username, "password": password}
    return client.post("/api/v1/invites/redeem", json=body, headers=CSRF)


def test_an_invite_creates_a_logged_in_account_with_its_role(client, db):
    token = new_invite(db, users.ADMIN)

    response = redeem(client, token)

    assert response.status_code == 201
    assert response.json["user"]["username"] == "carol"
    assert response.json["user"]["role"] == "admin"
    assert "sbm_session=" in response.headers["Set-Cookie"]
    assert client.get("/api/v1/session").json["user"]["username"] == "carol"
    user = users.by_username(db, "carol")
    assert db[INVITES].find_one()["used_by"] == user["_id"]


def test_an_invite_works_once(client, app, db):
    token = new_invite(db)
    redeem(client, token)

    response = redeem(app.test_client(), token, "dave")

    assert response.status_code == 400
    assert response.json["code"] == "invalid_token"


def test_an_expired_invite_does_not_work(client, db, clock):
    token = new_invite(db, valid=timedelta(days=1))
    clock.advance(timedelta(days=1))

    assert redeem(client, token).json["code"] == "invalid_token"


def test_a_taken_name_keeps_the_invite_usable(client, db):
    add_user(db, "Carol")
    token = new_invite(db)

    taken = redeem(client, token, "carol")
    assert taken.status_code == 409
    assert taken.json == {
        "code": "username_taken",
        "message": "the name is taken",
        "field": "username",
    }

    assert redeem(client, token, "carol2").status_code == 201


def test_names_passwords_and_tokens_are_checked(client, db):
    token = new_invite(db)
    cases = [
        ({"username": "ab"}, "username"),
        ({"username": "-carol"}, "username"),
        ({"username": "carol smith"}, "username"),
        ({"username": "c" * 33}, "username"),
        ({"password": "too short"}, "password"),
        ({"password": "x" * 129}, "password"),
        ({"token": "not a token"}, "token"),
    ]
    for change, field in cases:
        body = {"token": token, "username": "carol", "password": NEW_PASSWORD} | change
        response = client.post("/api/v1/invites/redeem", json=body, headers=CSRF)
        assert response.status_code == 400, change
        assert response.json["field"] == field
    assert redeem(client, token).status_code == 201
