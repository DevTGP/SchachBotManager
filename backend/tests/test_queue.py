from datetime import timedelta

from sbm.referee import STANDARD_FEN
from sbm_store import jobs, matches, play, queue_settings
from sbm_store.names import JOBS

from stored_games import BLITZ, NOW, finish_by_resignation, start_with_opening

# Blitz without history: 2 * 10 s startup + 180 s + 80 * 2 s increment.
FALLBACK = timedelta(seconds=360)


def claim_next(db) -> dict:
    return jobs.claim(db, jobs.MATCH, "worker", now=NOW, lease=timedelta(minutes=1))


def test_empty_queue(client):
    response = client.get("/api/v1/queue")
    assert response.status_code == 200
    assert response.json == {"paused": False, "running": [], "waiting": [], "waiting_total": 0}


def test_waiting_matches_follow_one_another(client, enqueue):
    first = enqueue(now=NOW - timedelta(minutes=2))
    second = enqueue(now=NOW - timedelta(minutes=1))
    queue = client.get("/api/v1/queue").json
    assert [entry["match"]["id"] for entry in queue["waiting"]] == [str(first), str(second)]
    assert [entry["position"] for entry in queue["waiting"]] == [1, 2]
    assert queue["waiting"][0]["estimated_start"] == "2026-05-01T12:00:00.000Z"
    assert queue["waiting"][0]["estimated_end"] == "2026-05-01T12:06:00.000Z"
    assert queue["waiting"][1]["estimated_start"] == "2026-05-01T12:06:00.000Z"
    assert queue["waiting_total"] == 2


def test_higher_priority_goes_first(client, enqueue):
    enqueue(now=NOW - timedelta(minutes=2))
    urgent = enqueue(now=NOW - timedelta(minutes=1), priority=500)
    queue = client.get("/api/v1/queue").json
    assert queue["waiting"][0]["match"]["id"] == str(urgent)


def test_running_match_delays_the_waiting_ones(client, db, enqueue):
    running = enqueue(now=NOW - timedelta(minutes=3))
    waiting = enqueue(now=NOW - timedelta(minutes=2))
    claim_next(db)
    start_with_opening(db, running, NOW - timedelta(minutes=1))
    queue = client.get("/api/v1/queue").json
    assert [entry["match"]["id"] for entry in queue["running"]] == [str(running)]
    entry = queue["running"][0]
    assert entry["position"] == 0
    assert entry["estimated_start"] == "2026-05-01T11:59:00.000Z"
    assert entry["estimated_end"] == "2026-05-01T12:05:00.000Z"
    assert queue["waiting"][0]["match"]["id"] == str(waiting)
    assert queue["waiting"][0]["estimated_start"] == "2026-05-01T12:05:00.000Z"


def test_overdue_running_match_ends_now(client, db, enqueue):
    running = enqueue(now=NOW - timedelta(hours=1))
    claim_next(db)
    start_with_opening(db, running, NOW - timedelta(minutes=30))
    entry = client.get("/api/v1/queue").json["running"][0]
    assert entry["estimated_end"] == "2026-05-01T12:00:00.000Z"


def test_estimates_use_finished_games(client, db, enqueue):
    played = enqueue(now=NOW - timedelta(hours=1))
    job = claim_next(db)
    # Finishes two minutes after its start.
    finish_by_resignation(db, played, NOW - timedelta(minutes=30))
    jobs.complete(db, job["_id"], "worker", NOW - timedelta(minutes=28))
    enqueue()
    entry = client.get("/api/v1/queue").json["waiting"][0]
    assert entry["estimated_end"] == "2026-05-01T12:02:00.000Z"


def test_retried_match_waits_for_its_delay(client, db, enqueue):
    match_id = enqueue(now=NOW - timedelta(minutes=5))
    db[JOBS].update_one(
        {"payload.match_id": match_id}, {"$set": {"not_before": NOW + timedelta(seconds=30)}}
    )
    entry = client.get("/api/v1/queue").json["waiting"][0]
    assert entry["estimated_start"] == "2026-05-01T12:00:30.000Z"


def test_reports_a_paused_queue(client, db):
    queue_settings.set_paused(db, True)
    assert client.get("/api/v1/queue").json["paused"] is True


def test_skips_jobs_without_match(client, db, enqueue):
    match_id = enqueue()
    db["matches"].delete_one({"_id": match_id})
    queue = client.get("/api/v1/queue").json
    assert queue["waiting"] == []
    assert queue["waiting_total"] == 1


def test_games_of_people_run_beside_the_queue(client, db, reference_bots, enqueue):
    waiting = enqueue(now=NOW - timedelta(minutes=2))
    person = play.seat_side(play.HUMAN, "Guest", user_id=None, seat_hash="hash")
    game = play.create(
        db,
        play.HUMAN,
        person,
        matches.side(reference_bots[0]),
        BLITZ,
        start_fen=STANDARD_FEN,
        now=NOW - timedelta(minutes=3),
    )
    matches.start(db, game, NOW - timedelta(minutes=1))

    queue = client.get("/api/v1/queue").json

    assert [entry["match"]["id"] for entry in queue["running"]] == [str(game)]
    assert queue["running"][0]["match"]["type"] == "human"
    assert queue["running"][0]["estimated_end"] == "2026-05-01T12:05:00.000Z"
    assert queue["waiting"][0]["match"]["id"] == str(waiting)
    assert queue["waiting"][0]["estimated_start"] == "2026-05-01T12:00:00.000Z"
