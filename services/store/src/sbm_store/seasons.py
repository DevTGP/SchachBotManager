"""The seasons collection: planned → running → finished (E132).

A planned season waits for starts_after; the first one of a league has None there until an
admin releases it. The start writes the lineup into tiers ({tier, entries}), each entry with
bot_id, name, version and lot, and a copy of the league's settings with its discipline as
discipline_snapshot. The schedule follows and is confirmed by scheduled. The end stores the
final tables in final ({tier, table}).
"""

from datetime import datetime

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from sbm_store.names import SEASONS

SCHEMA_VERSION = 1
PLANNED = "planned"
RUNNING = "running"
FINISHED = "finished"


def new_season(
    league_id: ObjectId,
    number: int,
    *,
    starts_after: datetime | None,
    seeds: list[list[ObjectId]],
    now: datetime,
) -> dict:
    return {
        "_id": ObjectId(),
        "schema_version": SCHEMA_VERSION,
        "league_id": league_id,
        "number": number,
        "status": PLANNED,
        "starts_after": starts_after,
        "seeds": seeds,
        "settings": None,
        "tiers": [],
        "withdrawn": [],
        "scheduled": False,
        "final": None,
        "created_at": now,
        "started_at": None,
        "finished_at": None,
    }


def insert(db: Database, season: dict) -> bool:
    """False if the league has a season with this number already."""
    try:
        db[SEASONS].insert_one(season)
    except DuplicateKeyError:
        return False
    return True


def get(db: Database, season_id: ObjectId) -> dict | None:
    return db[SEASONS].find_one({"_id": season_id})


def of_league(db: Database, league_id: ObjectId) -> list[dict]:
    """All seasons of a league, newest first."""
    return list(db[SEASONS].find({"league_id": league_id}).sort("number", DESCENDING))


def latest(db: Database, league_id: ObjectId) -> dict | None:
    return db[SEASONS].find_one({"league_id": league_id}, sort=[("number", DESCENDING)])


def release(db: Database, league_id: ObjectId, now: datetime) -> bool:
    """Lets the first season start (E132); False if no season waits for a release."""
    result = db[SEASONS].update_one(
        {"league_id": league_id, "status": PLANNED, "starts_after": None},
        {"$set": {"starts_after": now}},
    )
    return result.modified_count == 1


def due(db: Database, now: datetime) -> list[dict]:
    query = {"status": PLANNED, "starts_after": {"$ne": None, "$lte": now}}
    return list(db[SEASONS].find(query).sort([("starts_after", ASCENDING), ("_id", ASCENDING)]))


def begin(
    db: Database, season_id: ObjectId, *, settings: dict, tiers: list[dict], now: datetime
) -> dict | None:
    """Starts a planned season; returns it as it is now, None if it is not planned (any more)."""
    result = db[SEASONS].update_one(
        {"_id": season_id, "status": PLANNED},
        {
            "$set": {
                "status": RUNNING,
                "settings": settings,
                "tiers": tiers,
                "scheduled": False,
                "started_at": now,
            }
        },
    )
    return get(db, season_id) if result.modified_count == 1 else None


def mark_scheduled(db: Database, season_id: ObjectId) -> None:
    db[SEASONS].update_one({"_id": season_id}, {"$set": {"scheduled": True}})


def running(db: Database) -> list[dict]:
    return list(db[SEASONS].find({"status": RUNNING}).sort("_id", ASCENDING))


def running_with_bot(
    db: Database, bot_id: ObjectId, league_id: ObjectId | None = None
) -> list[dict]:
    query: dict = {"status": RUNNING, "tiers.entries.bot_id": bot_id}
    if league_id is not None:
        query["league_id"] = league_id
    return list(db[SEASONS].find(query))


def add_withdrawn(db: Database, season_id: ObjectId, bot_id: ObjectId) -> None:
    db[SEASONS].update_one({"_id": season_id}, {"$addToSet": {"withdrawn": bot_id}})


def finish(db: Database, season_id: ObjectId, final: list[dict], now: datetime) -> bool:
    result = db[SEASONS].update_one(
        {"_id": season_id, "status": RUNNING},
        {"$set": {"status": FINISHED, "final": final, "finished_at": now}},
    )
    return result.modified_count == 1


def tier_of(season: dict, bot_id: ObjectId) -> int | None:
    """The tier of a bot in a started season; None if it does not play in it."""
    for tier in season["tiers"]:
        if any(entry["bot_id"] == bot_id for entry in tier["entries"]):
            return tier["tier"]
    return None
