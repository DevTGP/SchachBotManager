"""The tournaments collection: the settings of each tournament (E172).

Like leagues: names are unique regardless of case through name_key, a tournament is archived,
never deleted, and an edition copies the settings at its start (snapshot), so changes apply from
the next edition. The format is fixed once the tournament exists; the calendar (recurrence,
E171) is not copied.
"""

from datetime import datetime

from bson import ObjectId
from pymongo import ASCENDING, ReturnDocument
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from sbm_store.names import TOURNAMENTS

SCHEMA_VERSION = 1
ROUND_ROBIN = "round_robin"
SWISS = "swiss"
KNOCKOUT = "knockout"
FORMATS = (ROUND_ROBIN, SWISS, KNOCKOUT)
# Points are fixed for tournaments (E172).
POINTS = {"win": 1, "draw": 0.5, "loss": 0}
# The settings an admin sets, with their defaults; name, discipline_id and format have none.
DEFAULTS = {
    "games_per_pairing": 2,
    "rounds": 5,
    "tiebreak_discipline_id": None,
    "tiebreak_pairs": 1,
    "min_participants": 2,
    "priority": 40,
    "recurrence": None,
}
DEFAULT_TIEBREAKS = {
    ROUND_ROBIN: ["wins", "head_to_head", "sonneborn_berger"],
    SWISS: ["buchholz", "sonneborn_berger", "wins"],
    KNOCKOUT: [],
}
SETTINGS = (
    "discipline_id",
    "format",
    "games_per_pairing",
    "rounds",
    "tiebreaks",
    "tiebreak_discipline_id",
    "tiebreak_pairs",
    "min_participants",
    "priority",
)


class NameTaken(Exception):
    """Another tournament has this name already."""


def name_key(name: str) -> str:
    return name.lower()


def new_tournament(fields: dict, *, created_by: ObjectId | None, now: datetime) -> dict:
    """fields holds name, discipline_id and format and any settings that differ from the
    defaults; the tiebreaks default to those of the format."""
    return {
        "_id": ObjectId(),
        "schema_version": SCHEMA_VERSION,
        **DEFAULTS,
        "tiebreaks": list(DEFAULT_TIEBREAKS[fields["format"]]),
        **fields,
        "name_key": name_key(fields["name"]),
        "archived": False,
        "created_by": created_by,
        "created_at": now,
        "updated_at": now,
    }


def insert(db: Database, tournament: dict) -> bool:
    """False if the name is taken."""
    try:
        db[TOURNAMENTS].insert_one(tournament)
    except DuplicateKeyError:
        return False
    return True


def get(db: Database, tournament_id: ObjectId) -> dict | None:
    return db[TOURNAMENTS].find_one({"_id": tournament_id})


def all_by_name(db: Database) -> list[dict]:
    return list(db[TOURNAMENTS].find().sort([("name_key", ASCENDING)]))


def by_ids(db: Database, tournament_ids: list[ObjectId]) -> dict[ObjectId, dict]:
    found = db[TOURNAMENTS].find({"_id": {"$in": tournament_ids}})
    return {tournament["_id"]: tournament for tournament in found}


def update(db: Database, tournament_id: ObjectId, fields: dict, *, now: datetime) -> dict | None:
    """Sets settings and/or archived; returns the tournament as it is now, None if there is none.

    Raises NameTaken if a new name belongs to another tournament.
    """
    changes = dict(fields)
    if "name" in changes:
        changes["name_key"] = name_key(changes["name"])
    try:
        return db[TOURNAMENTS].find_one_and_update(
            {"_id": tournament_id},
            {"$set": changes | {"updated_at": now}},
            return_document=ReturnDocument.AFTER,
        )
    except DuplicateKeyError as error:
        raise NameTaken(fields["name"]) from error


def settings(tournament: dict) -> dict:
    """The settings an edition copies at its start."""
    return {field: tournament[field] for field in SETTINGS}
