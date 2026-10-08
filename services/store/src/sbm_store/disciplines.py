"""The disciplines collection: time controls and limits that matches copy (E100).

Names are unique regardless of case through name_key. Disciplines are archived, never deleted;
an archived discipline stays readable but nothing new may use it.
"""

from datetime import datetime

from bson import ObjectId
from pymongo import ASCENDING, ReturnDocument
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from sbm_store.discipline import Discipline
from sbm_store.names import DISCIPLINES

SCHEMA_VERSION = 1
# The fields of a Discipline that an admin sets; discipline_id is the document's _id.
SETTINGS = (
    "name",
    "initial_time_ms",
    "increment_ms",
    "startup_ms",
    "tolerance_ms",
    "max_moves",
)


class NameTaken(Exception):
    """Another discipline has this name already."""


def name_key(name: str) -> str:
    return name.lower()


def new_discipline(discipline: Discipline, *, created_by: ObjectId | None, now: datetime) -> dict:
    settings = {field: getattr(discipline, field) for field in SETTINGS}
    return {
        "_id": ObjectId(),
        "schema_version": SCHEMA_VERSION,
        **settings,
        "name_key": name_key(discipline.name),
        "archived": False,
        "created_by": created_by,
        "created_at": now,
        "updated_at": now,
    }


def insert(db: Database, discipline: dict) -> bool:
    """False if the name is taken."""
    try:
        db[DISCIPLINES].insert_one(discipline)
    except DuplicateKeyError:
        return False
    return True


def get(db: Database, discipline_id: ObjectId) -> dict | None:
    return db[DISCIPLINES].find_one({"_id": discipline_id})


def all_by_name(db: Database, *, archived: bool = True) -> list[dict]:
    """All disciplines by name; without the archived ones if archived is False."""
    query = {} if archived else {"archived": False}
    return list(db[DISCIPLINES].find(query).sort([("name_key", ASCENDING)]))


def update(db: Database, discipline_id: ObjectId, fields: dict, *, now: datetime) -> dict | None:
    """Sets settings and/or archived; returns the discipline as it is now, None if there is none.

    Raises NameTaken if a new name belongs to another discipline.
    """
    changes = dict(fields)
    if "name" in changes:
        changes["name_key"] = name_key(changes["name"])
    try:
        return db[DISCIPLINES].find_one_and_update(
            {"_id": discipline_id},
            {"$set": changes | {"updated_at": now}},
            return_document=ReturnDocument.AFTER,
        )
    except DuplicateKeyError as error:
        raise NameTaken(fields["name"]) from error


def snapshot(discipline: dict) -> Discipline:
    """The discipline as a match copies it."""
    settings = {field: discipline[field] for field in SETTINGS}
    return Discipline(**settings, discipline_id=discipline["_id"])
