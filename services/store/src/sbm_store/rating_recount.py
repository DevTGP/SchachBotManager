"""Counting all ratings again from the stored matches, after matches were deleted (E105).

A request is a token in the settings collection. The runner sees it before its next job and
starts from scratch: every match uncounted, every bot and account back at the start, then all
rated matches in the order they finished (ratings.count_pending). It clears the token only if
no new request came in meanwhile; a crash midway leaves it set, so the next round starts over.
Only one worker may count at a time; the parallelism setting of the queue is not used yet, and
the play runner does not count while a request is open.
"""

from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import ratings
from sbm_store.names import BOTS, MATCHES, SETTINGS, USERS

DOCUMENT_ID = "ratings"


def request(db: Database, now: datetime) -> None:
    db[SETTINGS].update_one(
        {"_id": DOCUMENT_ID},
        {"$set": {"recount_request": ObjectId(), "requested_at": now}},
        upsert=True,
    )


def is_requested(db: Database) -> bool:
    return _pending(db) is not None


def run_if_requested(db: Database) -> int | None:
    """Counts everything again if asked to; returns how many matches, None if not asked."""
    document = _pending(db)
    if document is None:
        return None
    counted = recount(db)
    db[SETTINGS].update_one(
        {"_id": DOCUMENT_ID, "recount_request": document["recount_request"]},
        {"$set": {"recount_request": None}},
    )
    return counted


def recount(db: Database) -> int:
    # Matches first: once none is counted, nothing puts an old value back on a bot.
    db[MATCHES].update_many({"rating": {"$exists": True}}, {"$unset": {"rating": ""}})
    for collection in (BOTS, USERS):
        db[collection].update_many({"rating": {"$exists": True}}, {"$unset": {"rating": ""}})
    return ratings.count_pending(db)


def _pending(db: Database) -> dict | None:
    return db[SETTINGS].find_one({"_id": DOCUMENT_ID, "recount_request": {"$ne": None}})
