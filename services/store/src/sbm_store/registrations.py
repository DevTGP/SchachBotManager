"""The registrations collection: bots and accounts registered for a league (E136) or
tournament (E179, E182).

target_type tells the two apart; each function takes it as a keyword, leagues by default. A
registration names a bot by bot_id or an account by user_id, the other is None; functions take
the participant key (participants.key). At most one active registration per participant and
target, by a partial unique index. Leaving keeps the document as left with a reason, so the
history stays.
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
# Why a participant left: its owner or an admin deregistered it, the owner retired the bot, an
# admin disabled or deleted the bot, or deactivated the account (E182).
DEREGISTERED = "deregistered"
RETIRED = "retired"
DISABLED = "disabled"
DELETED = "deleted"
DEACTIVATED = "deactivated"
IN_ORDER = [("created_at", ASCENDING), ("_id", ASCENDING)]


def new_registration(
    target_id: ObjectId,
    bot_id: ObjectId | None = None,
    *,
    created_by: ObjectId,
    now: datetime,
    target_type: str = LEAGUE,
    user_id: ObjectId | None = None,
) -> dict:
    """A registration of a bot, or of the account user_id if bot_id is None."""
    return {
        "_id": ObjectId(),
        "schema_version": SCHEMA_VERSION,
        "target_type": target_type,
        "target_id": target_id,
        "bot_id": bot_id,
        "user_id": None if bot_id is not None else user_id,
        "status": ACTIVE,
        "created_at": now,
        "created_by": created_by,
        "left_at": None,
        "left_reason": None,
    }


def insert(db: Database, registration: dict) -> bool:
    """False if the participant is registered for the target already."""
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


def active_of_bot(db: Database, participant: ObjectId, *, target_type: str = LEAGUE) -> list[dict]:
    """The active registrations of a bot or account of one type."""
    query = {"target_type": target_type, "status": ACTIVE} | _of(participant)
    return list(db[REGISTRATIONS].find(query).sort(IN_ORDER))


def get_active(
    db: Database, target_id: ObjectId, participant: ObjectId, *, target_type: str = LEAGUE
) -> dict | None:
    query = {"target_type": target_type, "target_id": target_id, "status": ACTIVE}
    return db[REGISTRATIONS].find_one(query | _of(participant))


def leave(
    db: Database,
    participant: ObjectId,
    reason: str,
    now: datetime,
    *,
    target_type: str = LEAGUE,
    target_id: ObjectId | None = None,
) -> list[ObjectId]:
    """Ends the active registrations of a bot or account of one type, or only that for
    target_id; returns the targets."""
    query: dict = {"target_type": target_type, "status": ACTIVE} | _of(participant)
    if target_id is not None:
        query["target_id"] = target_id
    left = [registration["target_id"] for registration in db[REGISTRATIONS].find(query)]
    db[REGISTRATIONS].update_many(
        query, {"$set": {"status": LEFT, "left_at": now, "left_reason": reason}}
    )
    return left


def _of(participant: ObjectId) -> dict:
    return {"$or": [{"bot_id": participant}, {"user_id": participant}]}
