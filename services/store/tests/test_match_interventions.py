"""Cancelling a match and changing its priority (E152)."""

from datetime import timedelta

from conftest import BLITZ, START_FEN, T0

from sbm_store import jobs, matches
from sbm_store.enqueue import enqueue_match

LEASE = timedelta(seconds=60)


def enqueue(db, reference_bots, priority=100):
    return enqueue_match(db, *reference_bots, BLITZ, start_fen=START_FEN, now=T0, priority=priority)


def job_of(db, match_id):
    return db["jobs"].find_one({"payload.match_id": match_id})


def test_a_queued_job_is_cancelled_once(db, reference_bots):
    match_id = enqueue(db, reference_bots)

    cancelled = jobs.cancel_match(db, match_id, T0)

    assert cancelled["status"] == jobs.QUEUED
    assert job_of(db, match_id)["status"] == jobs.CANCELLED
    assert jobs.cancel_match(db, match_id, T0) is None
    assert jobs.claim(db, jobs.MATCH, "w1", now=T0, lease=LEASE) is None


def test_a_cancelled_running_job_is_no_longer_held(db, reference_bots):
    match_id = enqueue(db, reference_bots)
    job = jobs.claim(db, jobs.MATCH, "w1", now=T0, lease=LEASE)

    assert jobs.cancel_match(db, match_id, T0)["status"] == jobs.RUNNING

    assert not jobs.extend(db, job["_id"], "w1", T0 + LEASE)
    jobs.complete(db, job["_id"], "w1", T0)
    assert job_of(db, match_id)["status"] == jobs.CANCELLED
    assert jobs.expired(db, jobs.MATCH, T0 + 2 * LEASE) == []


def test_priority_changes_only_while_queued(db, reference_bots):
    first = enqueue(db, reference_bots, priority=100)
    second = enqueue(db, reference_bots, priority=100)

    assert jobs.set_match_priority(db, second, 200)
    claimed = jobs.claim(db, jobs.MATCH, "w1", now=T0, lease=LEASE)

    assert claimed["payload"]["match_id"] == second
    assert not jobs.set_match_priority(db, second, 300)
    assert jobs.set_match_priority(db, first, 100)


def test_abort_says_whether_the_match_was_still_open(db, reference_bots):
    match_id = enqueue(db, reference_bots)

    assert matches.abort(db, match_id, "cancelled by an admin", T0)
    assert not matches.abort(db, match_id, "cancelled by an admin", T0)


def test_the_match_mirrors_the_priority(db, reference_bots):
    match_id = enqueue(db, reference_bots)

    matches.set_priority(db, match_id, 7)

    assert matches.get(db, match_id)["queue"] == {"priority": 7}


def test_a_requester_cancels_only_while_queued(db, reference_bots):
    queued = enqueue(db, reference_bots)
    taken = enqueue(db, reference_bots, priority=200)
    jobs.claim(db, jobs.MATCH, "w1", now=T0, lease=LEASE)

    assert jobs.cancel_match(db, taken, T0, running=False) is None
    assert job_of(db, taken)["status"] == jobs.RUNNING
    assert jobs.cancel_match(db, queued, T0, running=False)["status"] == jobs.QUEUED
    assert job_of(db, queued)["status"] == jobs.CANCELLED
