from accounts import CSRF, PASSWORD

NEW_PASSWORD = "a long new password"


def change(client, current=PASSWORD, new=NEW_PASSWORD):
    body = {"current_password": current, "new_password": new}
    return client.put("/api/v1/account/password", json=body, headers=CSRF)


def test_changing_the_password_ends_the_other_sessions(app, login, db):
    client, user = login()
    other = app.test_client()
    other.post("/api/v1/session", json={"username": "coder", "password": PASSWORD}, headers=CSRF)

    assert change(client).status_code == 204

    assert client.get("/api/v1/session").json["user"]["username"] == "coder"
    assert other.get("/api/v1/session").json == {"user": None}
    login_again = app.test_client().post(
        "/api/v1/session", json={"username": "coder", "password": NEW_PASSWORD}, headers=CSRF
    )
    assert login_again.status_code == 200


def test_the_current_password_must_be_right(login):
    client, _ = login()

    response = change(client, current="wrong password")

    assert response.status_code == 401
    assert response.json["code"] == "invalid_credentials"


def test_the_new_password_must_be_long_enough(login):
    client, _ = login()

    response = change(client, new="short")

    assert response.status_code == 400
    assert response.json["field"] == "new_password"


def test_a_guest_cannot_change_a_password(client):
    response = change(client)

    assert response.status_code == 401
    assert response.json["code"] == "unauthenticated"
