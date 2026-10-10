"""Frees jobs of workers that died without handing them back."""

import logging
from datetime import datetime

from pymongo.database import Database
from sbm_store import jobs, matches

from sbm_runner.config import RunnerConfig
from sbm_runner.verification.rejection import reject_internal

log = logging.getLogger(__name__)


def recover_expired(db: Database, config: RunnerConfig, now: datetime) -> int:
    """Returns how many jobs it freed or gave up; a given-up verification rejects its bot
    unless it was a recheck (E153).

    A freed job's match is left as it is; the worker that claims the job next resets it (see
    game.run_job). Only the holder of a job touches its match, so recovery cannot reset a game
    that another worker has just started. A freed verification simply starts over.
    """
    handled = 0
    for job_type in (jobs.MATCH, jobs.VERIFICATION):
        for job in jobs.expired(db, job_type, now):
            if job["attempts"] < config.max_attempts:
                if jobs.requeue_expired(db, job):
                    log.warning(
                        "job %s lost its worker %s, queued again", job["_id"], job["worker_id"]
                    )
                    handled += 1
            elif jobs.fail_expired(db, job, now):
                _give_up(db, job, now)
                log.error("job %s lost its worker too often, given up", job["_id"])
                handled += 1
    return handled


def _give_up(db: Database, job: dict, now: datetime) -> None:
    if job["type"] == jobs.VERIFICATION:
        reject_internal(db, job, job["attempts"], now)
    else:
        detail = f"the runner stopped responding {job['attempts']} times"
        matches.abort(db, job["payload"]["match_id"], detail, now)
