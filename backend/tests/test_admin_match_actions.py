from datetime import timedelta

from bson import ObjectId
from sbm.referee import STANDARD_FEN
from sbm_store import bots, disciplines, jobs, matches, play
from sbm_store.enqueue import enqueue_match
from sbm_store.names import AUDIT_LOG, JOBS

from accounts import CSRF
from stored_disciplines import store_discipline
from stored_games import BLITZ, NOW, finish_by_resignation


def path(match_id, action: str = "") -> str:
    return f"/api/v1/admin/matches/{match_id}{action}"


def claim(db) -> dict:
    return jobs.claim(db, jobs.MATCH, "worker", now=NOW, lease=timedelta(minutes=1))


def job_of(db, match_id) -> dict:
    return db[JOBS].find_one({"payload.match_id": match_id})


def audit(db, action: str) -> dict:
    return db[AUDIT_LOG].find_one({"action": action})


def test_change_the_priority_of_a_waiting_match(admin, db, enqueue):
    match_id = enqueue()

    response = admin.patch(path(match_id), json={"priority": 700}, headers=CSRF)

    assert response.status_code == 200
    assert response.json == {"priority": 700}
    assert job_of(db, match_id)["priority"] == 700
    assert matches.get(db, match_id)["queue"]["priority"] == 700
    entry = audit(db, "match.priority")
    assert entry["target"] == match_id
    assert entry["details"] == {"priority": 700, "before": 100}


def test_the_priority_moves_it_to_the_front(admin, client, enqueue):
    enqueue(now=NOW - timedelta(minutes=2))
    later = enqueue(now=NOW - timedelta(minutes=1))

    admin.patch(path(later), json={"priority": 101}, headers=CSRF)

    waiting = client.get("/api/v1/queue").json["waiting"]
    assert waiting[0]["match"]["id"] == str(later)
    assert waiting[0]["priority"] == 101


def test_a_running_match_keeps_its_priority(admin, db, enqueue):
    match_id = enqueue()
    claim(db)
    matches.start(db, match_id, NOW)

    response = admin.patch(path(match_id), json={"priority": 700}, headers=CSRF)

    assert response.status_code == 409
    assert response.json["code"] == "match_state"
    assert job_of(db, match_id)["priority"] == 100


def test_invalid_priorities(admin, enqueue):
    match_id = enqueue()
    for body in ({"priority": -1}, {"priority": 1001}, {"priority": "high"}, {}):
        response = admin.patch(path(match_id), json=body, headers=CSRF)
        assert response.status_code == 400, body


def test_cancel_a_waiting_match(admin, db, enqueue):
    match_id = enqueue()

    response = admin.post(path(match_id, "/cancel"), headers=CSRF)

    assert response.status_code == 204
    match = matches.get(db, match_id)
    assert match["status"] == "aborted"
    assert match["result"] == "*"
    assert match["termination_detail"] == "cancelled by an admin"
    assert job_of(db, match_id)["status"] == jobs.CANCELLED
    assert claim(db) is None
    assert audit(db, "match.cancel")["details"] == {"status": "queued"}


def test_cancel_a_running_match(admin, db, enqueue):
    match_id = enqueue()
    claim(db)
    matches.start(db, match_id, NOW)

    response = admin.post(path(match_id, "/cancel"), headers=CSRF)

    assert response.status_code == 204
    assert matches.get(db, match_id)["status"] == "aborted"
    job = job_of(db, match_id)
    assert job["status"] == jobs.CANCELLED
    # The runner that held it cannot extend it any more and stops the game.
    assert not jobs.extend(db, job["_id"], "worker", NOW + timedelta(minutes=1))


def test_an_ended_match_cannot_be_cancelled(admin, db, enqueue):
    match_id = enqueue()
    claim(db)
    finish_by_resignation(db, match_id, NOW)

    response = admin.post(path(match_id, "/cancel"), headers=CSRF)

    assert response.status_code == 409
    assert response.json["code"] == "match_state"
    assert matches.get(db, match_id)["status"] == "finished"


def test_games_of_people_are_not_touched(admin, db, reference_bots):
    person = play.seat_side(play.HUMAN, "Guest", user_id=None, seat_hash="hash")
    game = play.create(
        db,
        play.HUMAN,
        person,
        matches.side(reference_bots[0]),
        BLITZ,
        start_fen=STANDARD_FEN,
        now=NOW,
    )

    for method, action in (("post", "/cancel"), ("post", "/repeat"), ("patch", "")):
        response = getattr(admin, method)(path(game, action), json={"priority": 1}, headers=CSRF)
        assert response.status_code == 409, action
        assert response.json["code"] == "match_state"


def test_unknown_matches(admin):
    for method, action in (("post", "/cancel"), ("post", "/repeat"), ("patch", "")):
        response = getattr(admin, method)(
            path(ObjectId(), action), json={"priority": 1}, headers=CSRF
        )
        assert response.status_code == 404, action


def test_repeat_an_ended_match(admin, db, reference_bots):
    white, black = reference_bots
    discipline = disciplines.snapshot(store_discipline(db, "Rapid", increment_ms=1_000))
    fen = "4k3/8/8/8/8/8/8/4K2R w K - 0 1"
    old = enqueue_match(db, black, white, discipline, start_fen=fen, now=NOW, priority=300)
    claim(db)
    finish_by_resignation(db, old, NOW)

    response = admin.post(path(old, "/repeat"), headers=CSRF)

    assert response.status_code == 201
    new_id = ObjectId(response.json["match_ids"][0])
    new = matches.get(db, new_id)
    assert new["status"] == "queued"
    assert new["white"]["name"] == "Material"
    assert new["black"]["name"] == "Random"
    assert new["start_fen"] == fen
    assert new["discipline_snapshot"]["name"] == "Rapid"
    assert new["queue"]["priority"] == 300
    assert job_of(db, new_id)["priority"] == 300
    entry = audit(db, "match.repeat")
    assert entry["target"] == new_id
    assert entry["details"] == {"from": str(old)}


def test_repeat_takes_the_discipline_as_it_is_now(admin, db, reference_bots):
    stored = store_discipline(db, "Rapid")
    old = enqueue_match(
        db, *reference_bots, disciplines.snapshot(stored), start_fen=STANDARD_FEN, now=NOW
    )
    matches.abort(db, old, "runner gone", NOW)
    disciplines.update(db, stored["_id"], {"initial_time_ms": 90_000}, now=NOW)

    new_id = admin.post(path(old, "/repeat"), headers=CSRF).json["match_ids"][0]

    snapshot = matches.get(db, ObjectId(new_id))["discipline_snapshot"]
    assert snapshot["initial_time_ms"] == 90_000


def test_a_waiting_match_cannot_be_repeated(admin, enqueue):
    response = admin.post(path(enqueue(), "/repeat"), headers=CSRF)

    assert response.status_code == 409
    assert response.json["code"] == "match_state"


def test_not_repeatable_without_a_verified_bot(admin, db, enqueue, reference_bots):
    match_id = enqueue()
    matches.abort(db, match_id, "runner gone", NOW)
    bots.set_enabled(db, reference_bots[1]["_id"], False)

    response = admin.post(path(match_id, "/repeat"), headers=CSRF)

    assert response.status_code == 409
    assert response.json["code"] == "not_repeatable"


def test_not_repeatable_with_an_archived_discipline(admin, db, reference_bots):
    stored = store_discipline(db, "Old", archived=True)
    old = enqueue_match(
        db, *reference_bots, disciplines.snapshot(stored), start_fen=STANDARD_FEN, now=NOW
    )
    matches.abort(db, old, "runner gone", NOW)

    response = admin.post(path(old, "/repeat"), headers=CSRF)

    assert response.status_code == 409
    assert response.json["code"] == "not_repeatable"


def test_repeat_keeps_an_unrated_game_unrated(admin, db, reference_bots):
    stored = disciplines.snapshot(store_discipline(db, "Rapid"))
    old = enqueue_match(db, *reference_bots, stored, start_fen=STANDARD_FEN, now=NOW, rated=False)
    matches.abort(db, old, "runner gone", NOW)

    new_id = admin.post(path(old, "/repeat"), headers=CSRF).json["match_ids"][0]

    new = matches.get(db, ObjectId(new_id))
    assert new["rated"] is False
    assert new["created_by"] == db["users"].find_one({"username": "admin"})["_id"]
    assert "series" not in new
