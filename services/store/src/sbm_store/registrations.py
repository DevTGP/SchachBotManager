"""The registrations collection: bots registered for a league (E136) or tournament (E179).

target_type tells the two apart; each function takes it as a keyword, leagues by default. At
most one active registration per bot and target, by a partial unique index. Leaving keeps
the document as left with a reason, so the history stays.
"""

from datetime import datetime

from bson import ObjectId
from pymongo import ASCENDING
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from sbm_store.names import REGISTRATIONS

SCHEMA_VERSION = 1
LEAGUE = "league"
TOURNAMENT = "tournament"
ACTIVE = "active"
LEFT = "left"
# Why a bot left: its owner or an admin deregistered it, the owner retired it, an admin
# disabled or deleted it.
DEREGISTERED = "deregistered"
RETIRED = "retired"
DISABLED = "disabled"
DELETED = "deleted"
IN_ORDER = [("created_at", ASCENDING), ("_id", ASCENDING)]


def new_registration(
    target_id: ObjectId,
    bot_id: ObjectId,
    *,
    created_by: ObjectId,
    now: datetime,
    target_type: str = LEAGUE,
) -> dict:
    return {
        "_id": ObjectId(),
        "schema_version": SCHEMA_VERSION,
        "target_type": target_type,
        "target_id": target_id,
        "bot_id": bot_id,
        "status": ACTIVE,
        "created_at": now,
        "created_by": created_by,
        "left_at": None,
        "left_reason": None,
    }


def insert(db: Database, registration: dict) -> bool:
    """False if the bot is registered for the target already."""
    try:
        db[REGISTRATIONS].insert_one(registration)
    except DuplicateKeyError:
        return False
    return True


def active_of_league(db: Database, target_id: ObjectId, *, target_type: str = LEAGUE) -> list[dict]:
    """The active registrations of a league or tournament in the order they came."""
    query = {"target_type": target_type, "target_id": target_id, "status": ACTIVE}
    return list(db[REGISTRATIONS].find(query).sort(IN_ORDER))


def count_active(db: Database, target_id: ObjectId, *, target_type: str = LEAGUE) -> int:
    query = {"target_type": target_type, "target_id": target_id, "status": ACTIVE}
    return db[REGISTRATIONS].count_documents(query)


def active_of_bot(db: Database, bot_id: ObjectId, *, target_type: str = LEAGUE) -> list[dict]:
    query = {"target_type": target_type, "bot_id": bot_id, "status": ACTIVE}
    return list(db[REGISTRATIONS].find(query).sort(IN_ORDER))


def get_active(
    db: Database, target_id: ObjectId, bot_id: ObjectId, *, target_type: str = LEAGUE
) -> dict | None:
    query = {"target_type": target_type, "target_id": target_id, "bot_id": bot_id, "status": ACTIVE}
    return db[REGISTRATIONS].find_one(query)


def leave(
    db: Database,
    bot_id: ObjectId,
    reason: str,
    now: datetime,
    *,
    target_type: str = LEAGUE,
    target_id: ObjectId | None = None,
) -> list[ObjectId]:
    """Ends the active registrations of a bot of one type, or only that for target_id; returns
    the targets."""
    query: dict = {"target_type": target_type, "bot_id": bot_id, "status": ACTIVE}
    if target_id is not None:
        query["target_id"] = target_id
    left = [registration["target_id"] for registration in db[REGISTRATIONS].find(query)]
    db[REGISTRATIONS].update_many(
        query, {"$set": {"status": LEFT, "left_at": now, "left_reason": reason}}
    )
    return left
