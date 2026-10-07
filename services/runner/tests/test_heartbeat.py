import time
from datetime import timedelta

from bson import ObjectId
from sbm_store import jobs

from sbm_runner.heartbeat import Heartbeat
from sbm_runner.worker import utc_now

LEASE = timedelta(seconds=60)
BEAT = timedelta(milliseconds=20)


def claimed_job(db) -> dict:
    jobs.insert(db, jobs.new_match_job(ObjectId(), priority=100, now=utc_now()))
    return jobs.claim(db, jobs.MATCH, "w1", now=utc_now(), lease=LEASE)


def wait_until(condition, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.01)
    return False


def test_renews_the_lease_while_the_game_runs(db):
    job = claimed_job(db)
    later = utc_now() + timedelta(hours=1)

    with Heartbeat(db, job["_id"], "w1", lease=LEASE, interval=BEAT, now=lambda: later):
        renewed = wait_until(lambda: db.jobs.find_one({"_id": job["_id"]})["lease_until"] > later)

    assert renewed


def test_stops_when_the_job_is_taken_away(db):
    job = claimed_job(db)
    jobs.release(db, job["_id"], "w1")

    heartbeat = Heartbeat(db, job["_id"], "w1", lease=LEASE, interval=BEAT, now=utc_now)
    with heartbeat:
        stopped = wait_until(lambda: not heartbeat._thread.is_alive())

    assert stopped
