"""The leagues collection: the settings of each league (E131).

Names are unique regardless of case through name_key. Leagues are archived, never deleted; an
archived league finishes its running season but starts no new one. A season copies the settings
at its start (snapshot), so changes apply from the next start; the calendar (recurrence, E171)
is not copied.
"""

from datetime import datetime

from bson import ObjectId
from pymongo import ASCENDING, ReturnDocument
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from sbm_store.names import LEAGUES

SCHEMA_VERSION = 1
# The settings an admin sets, with their defaults; name and discipline_id have none.
DEFAULTS = {
    "tiers": 1,
    "tier_size": 10,
    "games_per_pairing": 2,
    "promotions": 2,
    "points": {"win": 1, "draw": 0.5, "loss": 0},
    "tiebreaks": ["wins", "head_to_head", "sonneborn_berger"],
    "min_participants": 2,
    "priority": 50,
    # Hours an account has to declare readiness for a released game (E183).
    "ready_hours": 48,
    # The calendar (E171); not part of a season's snapshot.
    "recurrence": None,
}
SETTINGS = (
    "discipline_id",
    "tiers",
    "tier_size",
    "games_per_pairing",
    "promotions",
    "points",
    "tiebreaks",
    "min_participants",
    "priority",
    "ready_hours",
)


class NameTaken(Exception):
    """Another league has this name already."""


def name_key(name: str) -> str:
    return name.lower()


def new_league(fields: dict, *, created_by: ObjectId | None, now: datetime) -> dict:
    """fields holds name and discipline_id and any settings that differ from the defaults."""
    return {
        "_id": ObjectId(),
        "schema_version": SCHEMA_VERSION,
        **DEFAULTS,
        **fields,
        "name_key": name_key(fields["name"]),
        "archived": False,
        "created_by": created_by,
        "created_at": now,
        "updated_at": now,
    }


def insert(db: Database, league: dict) -> bool:
    """False if the name is taken."""
    try:
        db[LEAGUES].insert_one(league)
    except DuplicateKeyError:
        return False
    return True


def get(db: Database, league_id: ObjectId) -> dict | None:
    return db[LEAGUES].find_one({"_id": league_id})


def all_by_name(db: Database) -> list[dict]:
    return list(db[LEAGUES].find().sort([("name_key", ASCENDING)]))


def by_ids(db: Database, league_ids: list[ObjectId]) -> dict[ObjectId, dict]:
    return {league["_id"]: league for league in db[LEAGUES].find({"_id": {"$in": league_ids}})}


def update(db: Database, league_id: ObjectId, fields: dict, *, now: datetime) -> dict | None:
    """Sets settings and/or archived; returns the league as it is now, None if there is none.

    Raises NameTaken if a new name belongs to another league.
    """
    changes = dict(fields)
    if "name" in changes:
        changes["name_key"] = name_key(changes["name"])
    try:
        return db[LEAGUES].find_one_and_update(
            {"_id": league_id},
            {"$set": changes | {"updated_at": now}},
            return_document=ReturnDocument.AFTER,
        )
    except DuplicateKeyError as error:
        raise NameTaken(fields["name"]) from error


def settings(league: dict) -> dict:
    """The settings a season copies at its start."""
    return {field: league[field] for field in SETTINGS}
