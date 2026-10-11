"""The registrations collection: bots registered for a league (E136).

At most one active registration per bot and league, by a partial unique index. Leaving keeps
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
    league_id: ObjectId, bot_id: ObjectId, *, created_by: ObjectId, now: datetime
) -> dict:
    return {
        "_id": ObjectId(),
        "schema_version": SCHEMA_VERSION,
        "target_type": LEAGUE,
        "target_id": league_id,
        "bot_id": bot_id,
        "status": ACTIVE,
        "created_at": now,
        "created_by": created_by,
        "left_at": None,
        "left_reason": None,
    }


def insert(db: Database, registration: dict) -> bool:
    """False if the bot is registered for the league already."""
    try:
        db[REGISTRATIONS].insert_one(registration)
    except DuplicateKeyError:
        return False
    return True


def active_of_league(db: Database, league_id: ObjectId) -> list[dict]:
    """The active registrations of a league in the order they came."""
    query = {"target_type": LEAGUE, "target_id": league_id, "status": ACTIVE}
    return list(db[REGISTRATIONS].find(query).sort(IN_ORDER))


def count_active(db: Database, league_id: ObjectId) -> int:
    query = {"target_type": LEAGUE, "target_id": league_id, "status": ACTIVE}
    return db[REGISTRATIONS].count_documents(query)


def active_of_bot(db: Database, bot_id: ObjectId) -> list[dict]:
    query = {"target_type": LEAGUE, "bot_id": bot_id, "status": ACTIVE}
    return list(db[REGISTRATIONS].find(query).sort(IN_ORDER))


def get_active(db: Database, league_id: ObjectId, bot_id: ObjectId) -> dict | None:
    query = {"target_type": LEAGUE, "target_id": league_id, "bot_id": bot_id, "status": ACTIVE}
    return db[REGISTRATIONS].find_one(query)


def leave(
    db: Database,
    bot_id: ObjectId,
    reason: str,
    now: datetime,
    *,
    league_id: ObjectId | None = None,
) -> list[ObjectId]:
    """Ends the active registrations of a bot, or only that for league_id; returns the leagues."""
    query: dict = {"target_type": LEAGUE, "bot_id": bot_id, "status": ACTIVE}
    if league_id is not None:
        query["target_id"] = league_id
    left = [registration["target_id"] for registration in db[REGISTRATIONS].find(query)]
    db[REGISTRATIONS].update_many(
        query, {"$set": {"status": LEFT, "left_at": now, "left_reason": reason}}
    )
    return left
