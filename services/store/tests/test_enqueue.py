from datetime import timedelta

from conftest import BLITZ, START_FEN, T0

from sbm_store import jobs, matches
from sbm_store.enqueue import enqueue_match

LEASE = timedelta(minutes=1)


def test_enqueued_match_is_queued_with_a_job(db, reference_bots):
    white, black = reference_bots

    match_id = enqueue_match(db, white, black, BLITZ, start_fen=START_FEN, now=T0)

    match = matches.get(db, match_id)
    assert match["status"] == matches.QUEUED
    assert match["white"] == {
        "kind": "bot",
        "bot_id": white["_id"],
        "name": "Random",
        "sdk": None,
        "lang": None,
    }
    assert match["discipline_snapshot"]["initial_time_ms"] == 60_000
    waiting, total = jobs.waiting(db, jobs.MATCH, 10)
    assert total == 1
    assert waiting[0]["payload"] == {"match_id": match_id}


def test_jobs_start_by_priority_then_age(db, reference_bots):
    white, black = reference_bots

    def enqueue(seconds, **options):
        now = T0 + timedelta(seconds=seconds)
        return enqueue_match(db, white, black, BLITZ, start_fen=START_FEN, now=now, **options)

    first = enqueue(0)
    second = enqueue(1)
    urgent = enqueue(2, priority=200)

    claimed = []
    later = T0 + timedelta(minutes=1)
    while job := jobs.claim(db, jobs.MATCH, "w1", now=later, lease=LEASE):
        claimed.append(job["payload"]["match_id"])
    assert claimed == [urgent, first, second]
