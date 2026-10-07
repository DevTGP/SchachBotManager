from datetime import timedelta

from bson import ObjectId
from conftest import T0

from sbm_store import jobs

LEASE = timedelta(seconds=60)


def queued_job(db, *, now=T0) -> dict:
    job = jobs.new_match_job(ObjectId(), priority=100, now=now)
    jobs.insert(db, job)
    return job


def test_claim_takes_a_job_once(db):
    job = queued_job(db)

    claimed = jobs.claim(db, jobs.MATCH, "w1", now=T0, lease=LEASE)

    assert claimed["_id"] == job["_id"]
    assert claimed["status"] == jobs.RUNNING
    assert claimed["worker_id"] == "w1"
    assert claimed["attempts"] == 1
    assert claimed["lease_until"] == T0 + LEASE
    assert jobs.claim(db, jobs.MATCH, "w2", now=T0, lease=LEASE) is None


def test_jobs_not_yet_due_are_not_claimed(db):
    queued_job(db, now=T0 + timedelta(minutes=5))

    assert jobs.claim(db, jobs.MATCH, "w1", now=T0, lease=LEASE) is None


def test_only_the_holder_extends_and_completes(db):
    job = queued_job(db)
    jobs.claim(db, jobs.MATCH, "w1", now=T0, lease=LEASE)

    assert not jobs.extend(db, job["_id"], "w2", T0 + 2 * LEASE)
    assert jobs.extend(db, job["_id"], "w1", T0 + 2 * LEASE)
    jobs.complete(db, job["_id"], "w2", T0)
    assert [running["_id"] for running in jobs.running(db, jobs.MATCH)] == [job["_id"]]
    jobs.complete(db, job["_id"], "w1", T0)
    assert jobs.running(db, jobs.MATCH) == []


def test_released_job_is_queued_again_without_counting_the_attempt(db):
    job = queued_job(db)
    jobs.claim(db, jobs.MATCH, "w1", now=T0, lease=LEASE)

    jobs.release(db, job["_id"], "w1")

    again = jobs.claim(db, jobs.MATCH, "w1", now=T0, lease=LEASE)
    assert again["attempts"] == 1


def test_expired_lease_frees_the_job_once(db):
    job = queued_job(db)
    jobs.claim(db, jobs.MATCH, "w1", now=T0, lease=LEASE)

    assert jobs.expired(db, jobs.MATCH, T0 + LEASE / 2) == []
    [stale] = jobs.expired(db, jobs.MATCH, T0 + 2 * LEASE)
    assert stale["_id"] == job["_id"]
    assert jobs.requeue_expired(db, stale)
    assert not jobs.requeue_expired(db, stale)
    assert jobs.waiting(db, jobs.MATCH, 10)[1] == 1


def test_failed_job_is_not_claimed_again(db):
    job = queued_job(db)

    jobs.fail(db, job["_id"], T0)

    assert jobs.claim(db, jobs.MATCH, "w1", now=T0, lease=LEASE) is None


def test_retried_job_waits_until_it_is_due(db):
    job = queued_job(db)
    jobs.claim(db, jobs.MATCH, "w1", now=T0, lease=LEASE)

    jobs.retry(db, job["_id"], "w1", T0 + LEASE)

    assert jobs.claim(db, jobs.MATCH, "w1", now=T0, lease=LEASE) is None
    again = jobs.claim(db, jobs.MATCH, "w1", now=T0 + LEASE, lease=LEASE)
    assert again["attempts"] == 2


def test_expired_job_fails_once(db):
    queued_job(db)
    jobs.claim(db, jobs.MATCH, "w1", now=T0, lease=LEASE)
    [stale] = jobs.expired(db, jobs.MATCH, T0 + 2 * LEASE)

    assert jobs.fail_expired(db, stale, T0)
    assert not jobs.fail_expired(db, stale, T0)
    assert jobs.running(db, jobs.MATCH) == []
