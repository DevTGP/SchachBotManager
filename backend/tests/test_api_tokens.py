"""API tokens of coders and remote matches with them (E116)."""

import pytest
from bson import ObjectId
from sbm_store import matches, play, play_settings, tokens
from sbm_store.names import API_TOKENS

from accounts import CSRF
from stored_disciplines import store_discipline


def make_token(client, name: str = "laptop") -> dict:
    response = client.post("/api/v1/account/tokens", json={"name": name}, headers=CSRF)
    assert response.status_code == 201, response.json
    return response.json


def remote(client, token: str, *, address: str = "198.51.100.9", **body):
    request = {"opponent": "Material", "color": "white", "initial_time_ms": 60_000} | body
    request = {field: value for field, value in request.items() if value is not None}
    headers = CSRF | {"Authorization": f"Bearer {token}"}
    return client.post(
        "/api/v1/remote/matches",
        json=request,
        headers=headers,
        environ_base={"REMOTE_ADDR": address},
    )


def test_coders_make_list_and_revoke_tokens(login, db):
    coder, user = login()
    created = make_token(coder)

    assert created["token"].startswith("sbm_")
    stored = db[API_TOKENS].find_one()
    assert stored["token_hash"] == tokens.token_hash(created["token"])
    listed = coder.get("/api/v1/account/tokens").json["items"]
    assert [item["name"] for item in listed] == ["laptop"] and "token" not in listed[0]
    assert coder.delete(f"/api/v1/account/tokens/{created['id']}", headers=CSRF).status_code == 204
    assert coder.get("/api/v1/account/tokens").json["items"] == []
    assert coder.delete(f"/api/v1/account/tokens/{created['id']}", headers=CSRF).status_code == 404


def test_tokens_are_for_coders_only(login, client):
    player, _ = login("pat", "player")
    assert player.get("/api/v1/account/tokens").status_code == 403
    assert (
        player.post("/api/v1/account/tokens", json={"name": "x"}, headers=CSRF).status_code == 403
    )
    assert client.get("/api/v1/account/tokens").status_code == 401


@pytest.mark.parametrize("name", ["", "   ", "x" * 41, "tab\there"])
def test_token_names_are_checked(login, name):
    coder, _ = login()
    response = coder.post("/api/v1/account/tokens", json={"name": name}, headers=CSRF)
    assert response.status_code == 400


def test_at_most_ten_tokens(login):
    coder, _ = login()
    for number in range(10):
        make_token(coder, f"token {number}")
    response = coder.post("/api/v1/account/tokens", json={"name": "eleven"}, headers=CSRF)
    assert response.status_code == 400


def test_a_token_starts_a_remote_match(login, client, db, reference_bots):
    coder, user = login()
    token = make_token(coder)

    response = remote(client, token["token"], increment_ms=500)

    assert response.status_code == 201, response.json
    seat = response.json
    match = matches.get(db, ObjectId(seat["match_id"]))
    assert (match["type"], match["rated"]) == ("remote", False)
    assert (match["white"]["kind"], match["white"]["name"]) == ("remote", "coder")
    assert match["white"]["seat_hash"] == tokens.token_hash(seat["seat"])
    assert match["black"]["bot_id"] == reference_bots[1]["_id"]
    assert match["origin"]["token_id"] == ObjectId(token["id"])
    assert match["origin"]["user_id"] == user["_id"]
    assert coder.get("/api/v1/account/tokens").json["items"][0]["last_used_at"] is not None


def test_a_discipline_by_name(login, client, db, reference_bots):
    coder, _ = login()
    token = make_token(coder)["token"]
    store_discipline(db, "Blitz", initial_time_ms=180_000, increment_ms=2000)

    response = remote(client, token, discipline="blitz", initial_time_ms=None)

    assert response.status_code == 201, response.json
    match = matches.get(db, ObjectId(response.json["match_id"]))
    assert match["discipline_snapshot"]["name"] == "Blitz"
    assert match["rated"] is False


@pytest.mark.parametrize(
    "body",
    [{"opponent": "Nobody"}, {"discipline": "Unknown", "initial_time_ms": None}, {"color": "red"}],
)
def test_invalid_remote_requests(login, client, reference_bots, body):
    coder, _ = login()
    token = make_token(coder)["token"]
    assert remote(client, token, **body).status_code == 400


def test_without_a_valid_token_nothing_starts(login, client, reference_bots):
    coder, _ = login()
    created = make_token(coder)
    assert remote(client, "sbm_" + "A" * 43).status_code == 401
    coder.delete(f"/api/v1/account/tokens/{created['id']}", headers=CSRF)
    assert remote(client, created["token"]).status_code == 401
    no_header = client.post(
        "/api/v1/remote/matches", json={"opponent": "Material", "color": "white"}, headers=CSRF
    )
    assert no_header.status_code == 401


def test_a_coder_who_became_a_player_loses_remote_games(login, client, db, reference_bots):
    coder, user = login()
    token = make_token(coder)["token"]
    db["users"].update_one({"_id": user["_id"]}, {"$set": {"role": "player"}})
    assert remote(client, token).status_code == 403


def test_one_remote_game_at_a_time_per_token(login, client, db, reference_bots):
    coder, _ = login()
    token = make_token(coder)["token"]
    play_settings.save(
        db, play_settings.PlaySettings(max_games=8, games_per_client=1, games_per_day=50)
    )
    assert remote(client, token).status_code == 201
    second = remote(client, token, address="198.51.100.10")
    assert (second.status_code, second.json["code"]) == (429, "too_many_games")
    assert play.active_count(db) == 1
