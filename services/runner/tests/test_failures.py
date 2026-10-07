"""Infrastructure errors, lost workers and shutdown."""

from datetime import timedelta

import pytest
from bson import ObjectId
from sbm_store import jobs, matches
from sbm_store.names import JOBS

from sbm_runner import game
from sbm_runner.recovery import recover_expired
from sbm_runner.shutdown import Shutdown
from sbm_runner.worker import Worker, utc_now


def job_of(db, match_id: ObjectId) -> dict:
    return db[JOBS].find_one({"payload.match_id": match_id})


class BrokenMatch:
    """Stands in for the referee and fails after the first move was recorded."""

    error: BaseException = RuntimeError("database gone")

    def __init__(self, white, black, settings, *, on_move):
        self._on_move = on_move

    def play(self):
        from sbm.referee import MoveRecord

        self._on_move(MoveRecord(1, "e2e4", "e4", "fen", 5, 9995, None))
        raise self.error


@pytest.fixture
def broken_match(monkeypatch):
    monkeypatch.setattr(game, "Match", BrokenMatch)
    return BrokenMatch


def test_infrastructure_error_retries_the_match_later(
    db, worker, reference_bots, enqueue, broken_match
):
    match_id = enqueue(*reference_bots)

    assert worker.step()

    match = matches.get(db, match_id)
    assert match["status"] == matches.QUEUED
    assert match["moves"] == []
    job = job_of(db, match_id)
    assert job["status"] == jobs.QUEUED
    assert job["not_before"] > utc_now() + timedelta(seconds=20)
    assert not worker.step()


def test_infrastructure_error_aborts_after_the_last_attempt(
    db, config, reference_bots, enqueue, broken_match
):
    match_id = enqueue(*reference_bots)
    db[JOBS].update_one({"payload.match_id": match_id}, {"$set": {"attempts": 2}})

    assert Worker(db, config).step()

    match = matches.get(db, match_id)
    assert match["status"] == matches.ABORTED
    assert "database gone" in match["termination_detail"]
    assert job_of(db, match_id)["status"] == jobs.FAILED


def test_shutdown_hands_the_match_back_without_counting(
    db, worker, reference_bots, enqueue, broken_match, monkeypatch
):
    monkeypatch.setattr(broken_match, "error", Shutdown("SIGTERM"))
    match_id = enqueue(*reference_bots)

    with pytest.raises(Shutdown):
        worker.step()

    assert matches.get(db, match_id)["status"] == matches.QUEUED
    job = job_of(db, match_id)
    assert (job["status"], job["attempts"]) == (jobs.QUEUED, 0)


def claim_as_dead_worker(db, config, match_id: ObjectId, *, attempts: int) -> None:
    """A worker that started the game and then vanished; its lease ran out long ago."""
    db[JOBS].update_one({"payload.match_id": match_id}, {"$set": {"attempts": attempts - 1}})
    past = utc_now() - timedelta(minutes=10)
    jobs.claim(db, jobs.MATCH, "dead-worker", now=past, lease=config.lease)
    matches.start(db, match_id, past)
    matches.append_move(db, match_id, {"ply": 1, "uci": "e2e4"})


def test_lost_worker_game_starts_over(db, worker, config, reference_bots, enqueue):
    match_id = enqueue(*reference_bots)
    claim_as_dead_worker(db, config, match_id, attempts=1)

    assert worker.step()

    match = matches.get(db, match_id)
    assert match["status"] == matches.FINISHED
    assert match["moves"][0]["ply"] == 1
    assert len(match["moves"]) == 6
    assert job_of(db, match_id)["attempts"] == 2


def test_lost_worker_too_often_aborts_the_match(db, config, reference_bots, enqueue):
    match_id = enqueue(*reference_bots)
    claim_as_dead_worker(db, config, match_id, attempts=config.max_attempts)

    assert recover_expired(db, config, utc_now()) == 1

    assert matches.get(db, match_id)["status"] == matches.ABORTED
    assert job_of(db, match_id)["status"] == jobs.FAILED


def test_live_lease_is_left_alone(db, config, reference_bots, enqueue):
    match_id = enqueue(*reference_bots)
    jobs.claim(db, jobs.MATCH, "busy-worker", now=utc_now(), lease=config.lease)

    assert recover_expired(db, config, utc_now()) == 0
    assert job_of(db, match_id)["worker_id"] == "busy-worker"
