"""POST /matches: single games set by coders for their own bots (E98)."""

from datetime import timedelta

import pytest
from bson import ObjectId
from sbm.referee import STANDARD_FEN
from sbm_store import bots, coder_settings, matches
from sbm_store.coder_settings import CoderSettings
from sbm_store.names import MATCHES

from accounts import CSRF
from bot_uploads import store_bot, verify
from stored_disciplines import store_discipline


@pytest.fixture
def own(login, db, reference_bots):
    """A coder's client and a verified bot of theirs."""
    coder, user = login()
    return coder, verify(db, store_bot(db, user["_id"]))


def enqueue(client, white, black, **body):
    request = {
        "white_bot_id": str(white["_id"]),
        "black_bot_id": str(black["_id"]),
        "initial_time_ms": 60_000,
    } | body
    return client.post("/api/v1/matches", json=request, headers=CSRF)


def test_queue_games_against_a_reference_bot(own, db, reference_bots):
    coder, bot = own

    response = enqueue(coder, bot, reference_bots[0], increment_ms=1000, games=3, alternate=True)

    assert response.status_code == 201
    queued = [matches.get(db, ObjectId(match_id)) for match_id in response.json["match_ids"]]
    assert [match["white"]["name"] for match in queued] == ["Sharp", "Random", "Sharp"]
    first = queued[0]
    assert first["discipline_snapshot"]["name"] == "60+1"
    assert first["discipline_snapshot"]["max_moves"] == 500
    assert first["queue"]["priority"] == 50
    assert first["start_fen"] == STANDARD_FEN
    assert first["white"]["version"] == "1.0.0"


def test_the_other_bot_may_be_foreign(own, db):
    coder, bot = own
    foreign = verify(db, store_bot(db, ObjectId(), name="Foreign"))
    assert enqueue(coder, foreign, bot).status_code == 201


def test_one_bot_must_be_your_own(own, reference_bots):
    coder, _ = own

    response = enqueue(coder, *reference_bots)

    assert (response.status_code, response.json["field"]) == (400, "white_bot_id")


def test_both_bots_must_be_verified(own, db):
    coder, bot = own
    retired = verify(db, store_bot(db, ObjectId(), name="Retired"))
    bots.change_by_owner(db, retired["_id"], retired=True)

    response = enqueue(coder, bot, retired)

    assert (response.status_code, response.json["field"]) == (400, "black_bot_id")


@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({"initial_time_ms": 300_001}, "initial_time_ms"),
        ({"increment_ms": 5001}, "increment_ms"),
        ({"games": 11}, "games"),
        ({"games": 0}, "games"),
        ({"priority": 100}, "priority"),
        ({"start_fen": "8/8/8/8/8/8/8/8 w - - 0 1"}, "start_fen"),
        ({"max_moves": 10}, "max_moves"),
    ],
)
def test_tight_limits(own, db, reference_bots, body, field):
    coder, bot = own

    response = enqueue(coder, bot, reference_bots[0], **body)

    assert (response.status_code, response.json["field"]) == (400, field)
    assert db[MATCHES].count_documents({}) == 0


def test_the_limits_and_the_priority_are_settings(own, db, reference_bots):
    coder_settings.save(
        db,
        CoderSettings(games_per_request=2, max_initial_ms=600_000, max_increment_ms=0, priority=30),
    )
    coder, bot = own
    random = reference_bots[0]

    assert enqueue(coder, bot, random, games=3).json["field"] == "games"
    assert enqueue(coder, bot, random, increment_ms=1).json["field"] == "increment_ms"
    response = enqueue(coder, bot, random, initial_time_ms=600_000, games=2)
    assert response.status_code == 201
    match = matches.get(db, ObjectId(response.json["match_ids"][0]))
    assert match["queue"]["priority"] == 30


def test_any_discipline_in_use_beyond_the_free_limits(own, db, reference_bots):
    coder, bot = own
    classical = store_discipline(db, "Classical", initial_time_ms=3_600_000, increment_ms=30_000)
    request = {
        "white_bot_id": str(bot["_id"]),
        "black_bot_id": str(reference_bots[0]["_id"]),
        "discipline_id": str(classical["_id"]),
    }

    response = coder.post("/api/v1/matches", json=request, headers=CSRF)

    assert response.status_code == 201
    match = matches.get(db, ObjectId(response.json["match_ids"][0]))
    assert match["discipline_snapshot"]["discipline_id"] == classical["_id"]
    assert match["rated"] is True
    free_times = request | {"discipline_id": None, "initial_time_ms": 60_000}
    free = coder.post("/api/v1/matches", json=free_times, headers=CSRF).json["match_ids"][0]
    assert matches.get(db, ObjectId(free))["rated"] is False


def test_archived_disciplines_are_out(own, db, reference_bots):
    coder, bot = own
    old = store_discipline(db, "Old", archived=True)

    response = enqueue(coder, bot, reference_bots[0], discipline_id=str(old["_id"]))

    assert (response.status_code, response.json["field"]) == (400, "discipline_id")


def test_games_are_limited_per_day(own, db, reference_bots, clock):
    coder_settings.save(db, CoderSettings(games_per_day=5))
    coder, bot = own
    random = reference_bots[0]
    assert enqueue(coder, bot, random, games=3).status_code == 201

    response = enqueue(coder, bot, random, games=3)

    assert response.status_code == 429
    assert response.json["code"] == "too_many_attempts"
    # The refused request costs nothing, so two more fit.
    assert enqueue(coder, bot, random, games=2).status_code == 201
    assert enqueue(coder, bot, random).status_code == 429
    clock.advance(timedelta(days=1))
    assert enqueue(coder, bot, random, games=5).status_code == 201


def test_needs_an_account(client, reference_bots):
    assert enqueue(client, *reference_bots).status_code == 401
