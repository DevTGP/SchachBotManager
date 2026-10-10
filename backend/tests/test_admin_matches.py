from bson import ObjectId
from sbm_store import matches
from sbm_store.names import AUDIT_LOG, BOTS

from accounts import CSRF
from stored_disciplines import store_discipline


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
        "rated": True,
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


def by_discipline(admin, reference_bots, discipline_id, **body):
    white, black = reference_bots
    request = {
        "white_bot_id": str(white["_id"]),
        "black_bot_id": str(black["_id"]),
        "discipline_id": str(discipline_id),
    } | body
    return admin.post("/api/v1/admin/matches", json=request, headers=CSRF)


def test_a_stored_discipline_makes_the_game_rated(admin, client, db, reference_bots):
    blitz = store_discipline(db, "Blitz", initial_time_ms=180_000, increment_ms=2000)

    match_id = by_discipline(admin, reference_bots, blitz["_id"]).json["match_ids"][0]

    match = client.get(f"/api/v1/matches/{match_id}").json
    assert match["discipline"]["discipline_id"] == str(blitz["_id"])
    assert (match["discipline"]["name"], match["discipline"]["increment_ms"]) == ("Blitz", 2000)
    assert match["rated"] is True


def test_free_times_and_other_positions_are_unrated(admin, client, db, reference_bots):
    blitz = store_discipline(db, "Blitz")
    fen = "4k3/8/8/8/8/8/8/4K2R w K - 0 1"
    free = enqueue(admin, reference_bots).json["match_ids"][0]
    placed = by_discipline(admin, reference_bots, blitz["_id"], start_fen=fen)

    for match_id in (free, placed.json["match_ids"][0]):
        match = client.get(f"/api/v1/matches/{match_id}").json
        assert match["rated"] is False


def test_invalid_disciplines(admin, db, reference_bots):
    archived = store_discipline(db, "Old", archived=True)
    blitz = store_discipline(db, "Blitz")
    cases = [
        (archived["_id"], {}, "discipline_id"),
        (ObjectId(), {}, "discipline_id"),
        ("nope", {}, "discipline_id"),
        (blitz["_id"], {"initial_time_ms": 60_000}, "initial_time_ms"),
        (blitz["_id"], {"max_moves": 100}, "max_moves"),
    ]
    for discipline_id, body, field in cases:
        response = by_discipline(admin, reference_bots, discipline_id, **body)
        assert (response.status_code, response.json["field"]) == (400, field), body
    assert db.matches.count_documents({}) == 0


def test_pause_and_resume_the_queue(admin, client, db):
    response = admin.patch("/api/v1/admin/queue", json={"paused": True}, headers=CSRF)

    assert response.json == {"paused": True}
    assert client.get("/api/v1/queue").json["paused"] is True
    assert db[AUDIT_LOG].find_one({"action": "queue.pause"})["details"] == {"paused": True}

    admin.patch("/api/v1/admin/queue", json={"paused": False}, headers=CSRF)
    assert client.get("/api/v1/queue").json["paused"] is False
