"""POST /play and the limits of interactive games (E114, E115)."""

from datetime import timedelta

import pytest
from bson import ObjectId
from sbm.referee import STANDARD_FEN
from sbm_store import jobs, matches, play, play_settings, tokens
from sbm_store.names import AUDIT_LOG, JOBS

from accounts import CSRF
from stored_disciplines import store_discipline


def start(client, bot, *, address: str = "198.51.100.7", **body):
    request = {"bot_id": str(bot["_id"]), "color": "white", "initial_time_ms": 300_000} | body
    request = {field: value for field, value in request.items() if value is not None}
    return client.post(
        "/api/v1/play", json=request, headers=CSRF, environ_base={"REMOTE_ADDR": address}
    )


def test_a_guest_starts_a_game_and_gets_a_seat(client, db, reference_bots):
    response = start(client, reference_bots[1], increment_ms=2000)

    assert response.status_code == 201
    seat = response.json
    assert (seat["color"], seat["socket_path"]) == ("white", "/api/v1/play/socket")
    match = matches.get(db, ObjectId(seat["match_id"]))
    assert (match["type"], match["status"], match["rated"]) == ("human", "queued", False)
    assert match["white"]["name"] == "Guest" and match["white"]["user_id"] is None
    assert match["white"]["seat_hash"] == tokens.token_hash(seat["seat"])
    assert match["black"]["bot_id"] == reference_bots[1]["_id"]
    assert match["start_fen"] == STANDARD_FEN
    assert (
        match["discipline_snapshot"]["initial_time_ms"],
        match["discipline_snapshot"]["increment_ms"],
    ) == (300_000, 2000)
    assert match["origin"]["ip_key"] and "198.51.100.7" not in match["origin"]["ip_key"]
    assert db[JOBS].find_one({"payload.match_id": match["_id"]})["type"] == play.PLAY_JOB


def test_an_account_plays_under_its_name_and_a_discipline_is_rated(login, db, reference_bots):
    client, user = login("alice", "player")
    discipline = store_discipline(db, "Rapid", initial_time_ms=600_000)

    response = start(
        client,
        reference_bots[0],
        color="black",
        discipline_id=str(discipline["_id"]),
        initial_time_ms=None,
    )

    assert response.status_code == 201, response.json
    match = matches.get(db, ObjectId(response.json["match_id"]))
    assert (match["black"]["name"], match["black"]["user_id"]) == ("alice", user["_id"])
    assert match["rated"] is True
    assert match["origin"]["user_id"] == user["_id"]


def test_random_draws_a_color(client, reference_bots):
    assert start(client, reference_bots[0], color="random").json["color"] in ("white", "black")


@pytest.mark.parametrize(
    "body",
    [
        {"color": "green"},
        {"initial_time_ms": 1_800_001},
        {"initial_time_ms": 9_999},
        {"increment_ms": 30_001},
        {"start_fen": STANDARD_FEN},
    ],
)
def test_invalid_requests_are_refused(client, reference_bots, body):
    assert start(client, reference_bots[0], **body).status_code == 400


def test_only_verified_bots_can_be_played(client, db, reference_bots):
    db["bots"].update_one({"_id": reference_bots[0]["_id"]}, {"$set": {"status": "disabled"}})
    assert start(client, reference_bots[0]).status_code == 400


def test_one_game_at_a_time_per_address(client, reference_bots):
    assert start(client, reference_bots[0]).status_code == 201
    second = start(client, reference_bots[0])
    assert (second.status_code, second.json["code"]) == (429, "too_many_games")
    assert start(client, reference_bots[0], address="198.51.100.8").status_code == 201


def test_a_finished_game_frees_the_address(client, db, reference_bots, clock):
    first = start(client, reference_bots[0])
    matches.abort(db, ObjectId(first.json["match_id"]), "test", clock.now())
    assert start(client, reference_bots[0]).status_code == 201


def test_all_places_taken(client, db, reference_bots):
    play_settings.save(
        db, play_settings.PlaySettings(max_games=1, games_per_client=1, games_per_day=50)
    )
    assert start(client, reference_bots[0]).status_code == 201
    full = start(client, reference_bots[0], address="198.51.100.8")
    assert (full.status_code, full.json["code"]) == (503, "no_capacity")


def test_games_per_day_are_limited_and_refusals_cost_nothing(client, db, reference_bots, clock):
    play_settings.save(
        db, play_settings.PlaySettings(max_games=16, games_per_client=4, games_per_day=2)
    )
    assert start(client, reference_bots[0]).status_code == 201
    assert start(client, reference_bots[0]).status_code == 201
    third = start(client, reference_bots[0])
    assert (third.status_code, third.json["code"]) == (429, "too_many_attempts")
    assert int(third.headers["Retry-After"]) > 0
    clock.advance(timedelta(days=1))
    assert start(client, reference_bots[0]).status_code == 201


def test_games_against_people_are_not_public(client, db, reference_bots, enqueue):
    queued = enqueue()
    match_id = start(client, reference_bots[0]).json["match_id"]

    listed = client.get("/api/v1/matches").json
    assert [item["id"] for item in listed["items"]] == [str(queued)]
    by_bot = client.get(f"/api/v1/matches?bot_id={reference_bots[0]['_id']}").json
    assert match_id not in [item["id"] for item in by_bot["items"]]
    assert client.get(f"/api/v1/matches/{match_id}").status_code == 404
    assert client.get(f"/api/v1/matches/{match_id}/pgn").status_code == 404


def test_admins_read_and_set_the_limits(admin, db):
    assert admin.get("/api/v1/admin/play-settings").json == {
        "max_games": 2,
        "games_per_client": 1,
        "games_per_day": 50,
    }
    settings = {"max_games": 4, "games_per_client": 2, "games_per_day": 100}
    response = admin.put("/api/v1/admin/play-settings", json=settings, headers=CSRF)
    assert (response.status_code, response.json) == (200, settings)
    assert play_settings.get(db) == play_settings.PlaySettings(4, 2, 100)
    assert db[AUDIT_LOG].find_one({"action": "play.settings"})["details"] == settings


@pytest.mark.parametrize("settings", [{"max_games": 0}, {"max_games": 17}, {"games_per_day": 1001}])
def test_limits_are_checked(admin, settings):
    full = {"max_games": 2, "games_per_client": 1, "games_per_day": 50} | settings
    assert admin.put("/api/v1/admin/play-settings", json=full, headers=CSRF).status_code == 400


def test_only_admins_see_the_limits(client, login):
    assert client.get("/api/v1/admin/play-settings").status_code == 401
    coder, _ = login()
    assert coder.get("/api/v1/admin/play-settings").status_code == 403


def test_the_job_of_a_game_is_never_a_queue_job(client, db, reference_bots):
    start(client, reference_bots[0])
    assert db[JOBS].count_documents({"type": jobs.MATCH}) == 0
