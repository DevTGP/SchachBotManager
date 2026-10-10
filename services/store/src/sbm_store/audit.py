"""The audit_log collection: who did what as admin, and when (E85)."""

from datetime import datetime

from bson import ObjectId
from pymongo import DESCENDING
from pymongo.database import Database

from sbm_store.names import AUDIT_LOG

# The actor of actions from the command line, such as the first invite.
CLI = "cli"
NEWEST_FIRST = [("at", DESCENDING), ("_id", DESCENDING)]


def record(
    db: Database,
    *,
    actor_id: ObjectId | None,
    actor: str,
    action: str,
    target: ObjectId | str | None,
    details: dict | None = None,
    now: datetime,
) -> None:
    db[AUDIT_LOG].insert_one(
        {
            "at": now,
            "actor_id": actor_id,
            "actor": actor,
            "action": action,
            "target": target,
            "details": details or {},
        }
    )


def entry_filter(
    *,
    actor: str | None = None,
    action: str | None = None,
    target: ObjectId | str | None = None,
    since: datetime | None = None,
    before: datetime | None = None,
) -> dict:
    """Entries matching every given condition; since is inclusive, before exclusive."""
    query: dict = {}
    if actor is not None:
        query["actor"] = actor
    if action is not None:
        query["action"] = action
    if target is not None:
        query["target"] = target
    period = {}
    if since is not None:
        period["$gte"] = since
    if before is not None:
        period["$lt"] = before
    if period:
        query["at"] = period
    return query


def page(db: Database, query: dict, *, limit: int, offset: int) -> tuple[list[dict], int]:
    """Entries newest first, and how many the query matches in total."""
    collection = db[AUDIT_LOG]
    items = list(collection.find(query).sort(NEWEST_FIRST).skip(offset).limit(limit))
    return items, collection.count_documents(query)


def actions(db: Database) -> list[str]:
    return sorted(db[AUDIT_LOG].distinct("action"))


def actors(db: Database) -> list[str]:
    return sorted(db[AUDIT_LOG].distinct("actor"))
