"""POST /matches/{match_id}/withdraw: an account takes a waiting game it set back (E157)."""

from datetime import timedelta

import pytest
from bson import ObjectId
from sbm_store import coder_settings, jobs, matches
from sbm_store.coder_settings import CoderSettings
from sbm_store.names import JOBS

from accounts import CSRF
from bot_uploads import store_bot, verify
from stored_games import NOW


@pytest.fixture
def own(login, db, reference_bots):
    coder, user = login()
    return coder, verify(db, store_bot(db, user["_id"]))


def request(client, white, black, **body) -> list[ObjectId]:
    data = {
        "white_bot_id": str(white["_id"]),
        "black_bot_id": str(black["_id"]),
        "initial_time_ms": 60_000,
    } | body
    response = client.post("/api/v1/matches", json=data, headers=CSRF)
    assert response.status_code == 201
    return [ObjectId(match_id) for match_id in response.json["match_ids"]]


def withdraw(client, match_id):
    return client.post(f"/api/v1/matches/{match_id}/withdraw", headers=CSRF)


def job_of(db, match_id) -> dict:
    return db[JOBS].find_one({"payload.match_id": match_id})


def test_withdraw_a_waiting_game(own, db, reference_bots):
    coder, bot = own
    match_id = request(coder, bot, reference_bots[0])[0]

    response = withdraw(coder, match_id)

    assert response.status_code == 204
    match = matches.get(db, match_id)
    assert match["status"] == "aborted"
    assert match["termination_detail"] == "withdrawn by the requester"
    assert job_of(db, match_id)["status"] == jobs.CANCELLED
    assert withdraw(coder, match_id).status_code == 409


def test_a_withdrawn_game_gives_its_place_in_the_daily_limit_back(own, db, reference_bots):
    coder_settings.save(db, CoderSettings(games_per_day=2))
    coder, bot = own
    random = reference_bots[0]
    first, _ = request(coder, bot, random, games=2)
    data = {"white_bot_id": str(bot["_id"]), "black_bot_id": str(random["_id"])}
    full = coder.post("/api/v1/matches", json=data | {"initial_time_ms": 60_000}, headers=CSRF)
    assert full.status_code == 429

    assert withdraw(coder, first).status_code == 204

    assert len(request(coder, bot, random)) == 1


def test_a_running_game_is_played_out(own, db, reference_bots):
    coder, bot = own
    match_id = request(coder, bot, reference_bots[0])[0]
    jobs.claim(db, jobs.MATCH, "worker", now=NOW, lease=timedelta(minutes=1))

    response = withdraw(coder, match_id)

    assert response.status_code == 409
    assert response.json["code"] == "match_state"
    assert matches.get(db, match_id)["status"] == "queued"
    assert job_of(db, match_id)["status"] == jobs.RUNNING


def test_only_the_requester_withdraws(own, db, login, admin, reference_bots, enqueue):
    coder, bot = own
    match_id = request(coder, bot, reference_bots[0])[0]
    other, _ = login("other")

    assert withdraw(other, match_id).status_code == 404
    assert withdraw(admin, match_id).status_code == 404
    # Games without a requester, e.g. from before E156, belong to nobody.
    assert withdraw(coder, enqueue()).status_code == 404
    assert withdraw(coder, ObjectId()).status_code == 404
    assert matches.get(db, match_id)["status"] == "queued"


def test_needs_a_coder(client, login, enqueue):
    player, _ = login("pat", "player")
    match_id = enqueue()

    assert withdraw(client, match_id).status_code == 401
    assert withdraw(player, match_id).status_code == 403
