"""GET /series/{series_id}: the games of one request and the score (E155)."""

from bson import ObjectId
from sbm_store import matches

from accounts import CSRF
from bot_uploads import store_bot, verify
from stored_games import NOW


def finish(db, match_id, result: str) -> None:
    matches.start(db, match_id, NOW)
    matches.finish(
        db, match_id, sides={}, result=result, termination="checkmate", detail="", now=NOW
    )


def test_games_of_one_request_form_a_series(login, client, db, reference_bots):
    coder, user = login()
    bot = verify(db, store_bot(db, user["_id"], name="Sharp"))
    data = {
        "white_bot_id": str(bot["_id"]),
        "black_bot_id": str(reference_bots[0]["_id"]),
        "initial_time_ms": 60_000,
        "games": 3,
        "alternate": True,
    }
    queued = coder.post("/api/v1/matches", json=data, headers=CSRF).json
    ids = queued["match_ids"]
    first, second, _ = (ObjectId(match_id) for match_id in ids)
    finish(db, first, "1-0")
    finish(db, second, "1-0")

    place = client.get(f"/api/v1/matches/{ids[1]}").json["series"]
    response = client.get(f"/api/v1/series/{place['id']}")

    assert place["id"] == queued["series_id"]
    assert place["index"] == 2
    assert place["games"] == 3
    assert response.status_code == 200
    series = response.json
    assert series["games"] == 3
    assert series["counted"] == 2
    assert (series["a"]["name"], series["a"]["points"]) == ("Sharp", 1.0)
    assert (series["b"]["name"], series["b"]["points"]) == ("Random", 1.0)
    assert [match["id"] for match in series["matches"]] == ids
    assert [match["series"]["index"] for match in series["matches"]] == [1, 2, 3]


def test_a_draw_is_half_a_point_and_a_bot_may_play_itself(admin, client, db, reference_bots):
    random = reference_bots[0]
    data = {
        "white_bot_id": str(random["_id"]),
        "black_bot_id": str(random["_id"]),
        "initial_time_ms": 60_000,
        "games": 2,
        "alternate": True,
    }
    queued = admin.post("/api/v1/admin/matches", json=data, headers=CSRF).json
    ids, series_id = queued["match_ids"], queued["series_id"]
    finish(db, ObjectId(ids[0]), "1/2-1/2")
    finish(db, ObjectId(ids[1]), "1-0")

    series = client.get(f"/api/v1/series/{series_id}").json

    assert (series["a"]["points"], series["b"]["points"]) == (1.5, 0.5)


def test_single_games_have_no_series(admin, client, enqueue, reference_bots):
    match_id = enqueue()
    assert client.get(f"/api/v1/matches/{match_id}").json["series"] is None
    data = {
        "white_bot_id": str(reference_bots[0]["_id"]),
        "black_bot_id": str(reference_bots[1]["_id"]),
        "initial_time_ms": 60_000,
    }
    queued = admin.post("/api/v1/admin/matches", json=data, headers=CSRF).json
    assert queued["series_id"] is None


def test_unknown_series(client):
    assert client.get(f"/api/v1/series/{ObjectId()}").status_code == 404
    assert client.get("/api/v1/series/xyz").status_code == 400
