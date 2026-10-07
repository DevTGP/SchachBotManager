from bson import ObjectId
from sbm_store import matches
from sbm_store.names import AUDIT_LOG, BOTS

from accounts import CSRF


def enqueue(admin, reference_bots, **body):
    white, black = reference_bots
    request = {
        "white_bot_id": str(white["_id"]),
        "black_bot_id": str(black["_id"]),
        "initial_time_ms": 180_000,
    } | body
    return admin.post("/api/v1/admin/matches", json=request, headers=CSRF)


def test_queue_games_with_alternating_colours(admin, db, reference_bots):
    response = enqueue(
        admin, reference_bots, increment_ms=2000, games=3, alternate=True, priority=300
    )

    assert response.status_code == 201
    ids = [ObjectId(match_id) for match_id in response.json["match_ids"]]
    queued = [matches.get(db, match_id) for match_id in ids]
    assert [match["white"]["name"] for match in queued] == ["Random", "Material", "Random"]
    first = queued[0]
    assert first["discipline_snapshot"]["name"] == "180+2"
    assert first["discipline_snapshot"]["max_moves"] == 500
    assert first["queue"]["priority"] == 300
    entry = db[AUDIT_LOG].find_one({"action": "match.enqueue"})
    assert entry["details"] == {
        "white": "Random",
        "black": "Material",
        "discipline": "180+2",
        "games": 3,
    }


def test_the_queue_shows_them(admin, client, reference_bots):
    ids = enqueue(admin, reference_bots).json["match_ids"]

    waiting = client.get("/api/v1/queue").json["waiting"]

    assert [entry["match"]["id"] for entry in waiting] == ids


def test_a_start_position(admin, db, reference_bots):
    fen = "4k3/8/8/8/8/8/8/4K2R w K - 0 1"

    match_id = enqueue(admin, reference_bots, start_fen=fen).json["match_ids"][0]

    assert matches.get(db, ObjectId(match_id))["start_fen"] == fen


def test_invalid_requests(admin, db, reference_bots):
    unverified = db[BOTS].insert_one({"name": "x", "status": "pending"}).inserted_id
    cases = [
        ({"start_fen": "not a position"}, "start_fen"),
        ({"initial_time_ms": 999}, "initial_time_ms"),
        ({"games": 0}, "games"),
        ({"games": True}, "games"),
        ({"max_moves": 2001}, "max_moves"),
        ({"white_bot_id": "0123456789abcdef01234567"}, "white_bot_id"),
        ({"black_bot_id": str(unverified)}, "black_bot_id"),
        ({"colour": "white"}, "colour"),
    ]
    for body, field in cases:
        response = enqueue(admin, reference_bots, **body)
        assert response.status_code == 400, body
        assert response.json["field"] == field
    assert db.matches.count_documents({}) == 0


def test_pause_and_resume_the_queue(admin, client, db):
    response = admin.patch("/api/v1/admin/queue", json={"paused": True}, headers=CSRF)

    assert response.json == {"paused": True}
    assert client.get("/api/v1/queue").json["paused"] is True
    assert db[AUDIT_LOG].find_one({"action": "queue.pause"})["details"] == {"paused": True}

    admin.patch("/api/v1/admin/queue", json={"paused": False}, headers=CSRF)
    assert client.get("/api/v1/queue").json["paused"] is False
