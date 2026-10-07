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


def hit(db: Database, key: str, *, now: datetime, window: timedelta) -> Count:
    """Counts one request for key; returns the requests in this window, this one included."""
    seconds = int(window.total_seconds())
    start = int(now.timestamp()) // seconds * seconds
    resets_at = datetime.fromtimestamp(start + seconds, now.tzinfo)
    document_id = f"{key}:{start}"
    update = {"$inc": {"count": 1}, "$setOnInsert": {"expires_at": resets_at}}
    try:
        counter = _increment(db, document_id, update)
    except DuplicateKeyError:
        # Two first requests at once: one upsert loses, and now the document exists.
        counter = _increment(db, document_id, update)
    return Count(requests=counter["count"], resets_at=resets_at)


def _increment(db: Database, document_id: str, update: dict) -> dict:
    return db[RATE_LIMITS].find_one_and_update(
        {"_id": document_id}, update, upsert=True, return_document=ReturnDocument.AFTER
    )
