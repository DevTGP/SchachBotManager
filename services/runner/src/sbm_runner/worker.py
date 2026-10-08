"""The runner's main loop: recover, claim, then play a match or verify a bot, one at a time."""

import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime

from pymongo.database import Database
from pymongo.errors import PyMongoError
from sbm_store import jobs, matches, queue_settings, rating_recount, ratings

from sbm_runner.config import RunnerConfig
from sbm_runner.game import run_job
from sbm_runner.heartbeat import Heartbeat
from sbm_runner.players import PlayerFactory, plain_player
from sbm_runner.recovery import recover_expired
from sbm_runner.retries import retry_or_abort, retry_or_reject
from sbm_runner.shutdown import Shutdown
from sbm_runner.verification.pipeline import Verifier, run_verification

log = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(UTC)


class Worker:
    """Does one job at a time; the parallelism setting of the queue is not used yet.

    Without a verifier (no sandbox) the worker takes no verification jobs.
    """

    def __init__(
        self,
        db: Database,
        config: RunnerConfig,
        *,
        players: PlayerFactory = plain_player,
        verifier: Verifier | None = None,
        now: Callable[[], datetime] = utc_now,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._db = db
        self._config = config
        self._players = players
        self._verifier = verifier
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
        self._recount_ratings()
        if queue_settings.get(self._db).paused:
            return False
        job = self._claim()
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

    def _claim(self) -> dict | None:
        """Matches first; a verification that waited too long goes ahead (E89)."""
        now = self._now()

        def claim(job_type: str, created_before: datetime | None = None) -> dict | None:
            return jobs.claim(
                self._db,
                job_type,
                self._config.worker_id,
                now=now,
                lease=self._config.lease,
                created_before=created_before,
            )

        if self._verifier is None:
            return claim(jobs.MATCH)
        return (
            claim(jobs.VERIFICATION, now - self._config.verification_wait)
            or claim(jobs.MATCH)
            or claim(jobs.VERIFICATION)
        )

    def _work(self, job: dict) -> None:
        if job["type"] == jobs.VERIFICATION:
            self._verify(job)
        else:
            self._play(job)

    def _verify(self, job: dict) -> None:
        try:
            run_verification(self._db, job, verifier=self._verifier, now=self._now)
        except Shutdown:
            # The bot keeps its pipeline status; the next attempt starts from the beginning.
            jobs.release(self._db, job["_id"], self._config.worker_id)
            raise
        except Exception:
            log.exception("verification job %s failed (attempt %d)", job["_id"], job["attempts"])
            retry_or_reject(self._db, job, self._config, self._now())

    def _play(self, job: dict) -> None:
        try:
            run_job(self._db, job, players=self._players, now=self._now)
        except Shutdown:
            # Stopping is not the match's fault: it starts over and the attempt does not count.
            matches.requeue(self._db, job["payload"]["match_id"])
            jobs.release(self._db, job["_id"], self._config.worker_id)
            raise
        except Exception as error:
            log.exception("job %s failed (attempt %d)", job["_id"], job["attempts"])
            detail = f"infrastructure error: {type(error).__name__}: {error}"
            retry_or_abort(self._db, job, detail, self._config, self._now())
        else:
            self._count_ratings()

    def _recount_ratings(self) -> None:
        """Counts all ratings again after an admin deleted counted matches (E105)."""
        counted = rating_recount.run_if_requested(self._db)
        if counted is not None:
            log.info("ratings: counted again from %d match(es)", counted)

    def _count_ratings(self) -> None:
        """Counts every finished rated match not counted yet (E103), older ones included."""
        try:
            counted = ratings.count_pending(self._db)
        except PyMongoError as error:
            # The result is stored; the next finished match counts this one too.
            log.warning("ratings not counted: %s", error)
            return
        if counted:
            log.info("ratings: %d match(es) counted", counted)
