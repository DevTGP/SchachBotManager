"""What happens to a job that failed for infrastructure reasons."""

from datetime import datetime

from pymongo.database import Database
from sbm_store import jobs, matches

from sbm_runner.config import RunnerConfig
from sbm_runner.verification.rejection import reject_internal


def retry_or_abort(
    db: Database, job: dict, detail: str, config: RunnerConfig, now: datetime
) -> None:
    """The game starts over after a delay, or is aborted once max_attempts is reached.

    The match is reset before the job is handed back, so whoever claims the job next never sees a
    half-played game.
    """
    match_id = job["payload"]["match_id"]
    if job["attempts"] < config.max_attempts:
        matches.requeue(db, match_id)
        jobs.retry(db, job["_id"], job["worker_id"], now + config.retry_delay)
    else:
        matches.abort(db, match_id, detail, now)
        jobs.fail(db, job["_id"], now)


def retry_or_reject(db: Database, job: dict, config: RunnerConfig, now: datetime) -> None:
    """The verification starts over after a delay, or the bot is rejected (stage internal)."""
    if job["attempts"] < config.max_attempts:
        jobs.retry(db, job["_id"], job["worker_id"], now + config.retry_delay)
    else:
        reject_internal(db, job, job["attempts"], now)
        jobs.fail(db, job["_id"], now)
