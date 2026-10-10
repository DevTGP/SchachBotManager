"""Puts a single game between two bots into the queue (E71: tests and dev tools until M3)."""

from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import jobs, matches
from sbm_store.discipline import Discipline

DEFAULT_PRIORITY = 100


def enqueue_match(
    db: Database,
    white: dict,
    black: dict,
    discipline: Discipline,
    *,
    start_fen: str,
    now: datetime,
    priority: int = DEFAULT_PRIORITY,
    rated: bool = True,
    series: dict | None = None,
    created_by: ObjectId | None = None,
    counted: bool = False,
) -> ObjectId:
    """Creates the match, then its job; the match id is returned.

    Without transactions a crash in between leaves a queued match without a job. It never
    starts and shows as queued in the match list, which is harmless.
    """
    match = matches.new_match(
        white,
        black,
        discipline,
        start_fen=start_fen,
        priority=priority,
        now=now,
        rated=rated,
        series=series,
        created_by=created_by,
        counted=counted,
    )
    matches.insert(db, match)
    jobs.insert(db, jobs.new_match_job(match["_id"], priority=priority, now=now))
    return match["_id"]
