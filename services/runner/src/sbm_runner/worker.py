"""The runner's main loop: recover, claim, play, one game at a time."""

import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime

from pymongo.database import Database
from pymongo.errors import PyMongoError
from sbm_store import jobs, matches, queue_settings

from sbm_runner.config import RunnerConfig
from sbm_runner.game import run_job
from sbm_runner.heartbeat import Heartbeat
from sbm_runner.recovery import recover_expired
from sbm_runner.retries import retry_or_abort
from sbm_runner.shutdown import Shutdown

log = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(UTC)


class Worker:
    """Plays one game at a time; the parallelism setting of the queue is not used yet."""

    def __init__(
        self,
        db: Database,
        config: RunnerConfig,
        *,
        now: Callable[[], datetime] = utc_now,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._db = db
        self._config = config
        self._now = now
        self._sleep = sleep

    def run(self, should_stop: Callable[[], bool] = lambda: False) -> None:
        """Runs until should_stop says so or Shutdown is raised."""
        while not should_stop():
            try:
                worked = self.step()
            except PyMongoError as error:
                log.warning("database unavailable: %s", error)
                worked = False
            if not worked:
                self._sleep(self._config.poll_interval.total_seconds())

    def step(self) -> bool:
        """Does one round of work; False if there was nothing to do."""
        recover_expired(self._db, self._config, self._now())
        if queue_settings.get(self._db).paused:
            return False
        job = jobs.claim(
            self._db,
            jobs.MATCH,
            self._config.worker_id,
            now=self._now(),
            lease=self._config.lease,
        )
        if job is None:
            return False
        heartbeat = Heartbeat(
            self._db,
            job["_id"],
            self._config.worker_id,
            lease=self._config.lease,
            interval=self._config.heartbeat,
            now=self._now,
        )
        with heartbeat:
            self._work(job)
        return True

    def _work(self, job: dict) -> None:
        try:
            run_job(self._db, job, now=self._now)
        except Shutdown:
            # Stopping is not the match's fault: it starts over and the attempt does not count.
            matches.requeue(self._db, job["payload"]["match_id"])
            jobs.release(self._db, job["_id"], self._config.worker_id)
            raise
        except Exception as error:
            log.exception("job %s failed (attempt %d)", job["_id"], job["attempts"])
            detail = f"infrastructure error: {type(error).__name__}: {error}"
            retry_or_abort(self._db, job, detail, self._config, self._now())
