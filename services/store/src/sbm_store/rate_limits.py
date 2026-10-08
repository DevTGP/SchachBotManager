"""The rate_limits collection: counters per key in fixed time windows (E84).

One document per key and window; MongoDB removes it through a TTL index once the window ends.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from pymongo import ReturnDocument
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from sbm_store.names import RATE_LIMITS


@dataclass(frozen=True)
class Count:
    requests: int
    resets_at: datetime


def hit(db: Database, key: str, *, now: datetime, window: timedelta, amount: int = 1) -> Count:
    """Counts amount requests for key; returns the requests in this window, these included."""
    document_id, resets_at = _window(key, now, window)
    update = {"$inc": {"count": amount}, "$setOnInsert": {"expires_at": resets_at}}
    try:
        counter = _increment(db, document_id, update)
    except DuplicateKeyError:
        # Two first requests at once: one upsert loses, and now the document exists.
        counter = _increment(db, document_id, update)
    return Count(requests=counter["count"], resets_at=resets_at)


def give_back(db: Database, key: str, *, now: datetime, window: timedelta, amount: int) -> None:
    """Takes back amount requests that hit counted at the same now, e.g. a refused one."""
    document_id, _ = _window(key, now, window)
    db[RATE_LIMITS].update_one({"_id": document_id}, {"$inc": {"count": -amount}})


def _window(key: str, now: datetime, window: timedelta) -> tuple[str, datetime]:
    """The document id of the window that holds now, and when that window ends."""
    seconds = int(window.total_seconds())
    start = int(now.timestamp()) // seconds * seconds
    return f"{key}:{start}", datetime.fromtimestamp(start + seconds, now.tzinfo)


def _increment(db: Database, document_id: str, update: dict) -> dict:
    return db[RATE_LIMITS].find_one_and_update(
        {"_id": document_id}, update, upsert=True, return_document=ReturnDocument.AFTER
    )
