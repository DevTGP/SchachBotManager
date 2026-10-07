from datetime import timedelta

import pytest
from bson import ObjectId
from sbm.referee import STANDARD_FEN
from sbm_store import bots
from sbm_store.discipline import Discipline
from sbm_store.enqueue import enqueue_match
from sbm_store.migrate import migrate
from sbm_store.names import BOTS

from sbm_runner.config import RunnerConfig
from sbm_runner.worker import Worker, utc_now

# Short games: a few moves each side, so a real game between the reference bots takes a second.
QUICK = Discipline("Quick", initial_time_ms=10_000, increment_ms=0, max_moves=3)


@pytest.fixture
def config() -> RunnerConfig:
    return RunnerConfig(
        worker_id="test-worker",
        lease=timedelta(seconds=60),
        heartbeat=timedelta(seconds=15),
        retry_delay=timedelta(seconds=30),
    )


@pytest.fixture
def reference_bots(db) -> tuple[dict, dict]:
    migrate(db)
    return bots.by_name(db, "Random"), bots.by_name(db, "Material")


@pytest.fixture
def worker(db, config) -> Worker:
    return Worker(db, config, sleep=lambda _seconds: None)


@pytest.fixture
def enqueue(db):
    """Queues a game in the past, so it is due for every worker clock."""

    def enqueue(white: dict, black: dict, discipline: Discipline = QUICK) -> ObjectId:
        created = utc_now() - timedelta(hours=1)
        return enqueue_match(db, white, black, discipline, start_fen=STANDARD_FEN, now=created)

    return enqueue


@pytest.fixture
def foreign_bot(db) -> dict:
    """A bot that would need the sandbox (E72)."""
    bot = {
        "_id": ObjectId(),
        "name": "Uploaded",
        "language": "python",
        "source_ref": "uploads/abc",
        "status": bots.VERIFIED,
    }
    db[BOTS].insert_one(bot)
    return bot
