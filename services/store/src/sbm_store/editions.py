"""The editions collection: one run of a tournament, planned → running → finished (E173).

A planned edition waits for starts_after, the next date of the tournament's calendar (E171);
without a calendar it has None there until an admin starts it. The start writes a copy of the
settings with tournament_name, discipline_snapshot and tiebreak_discipline_snapshot, and the
participants by seed ({bot_id, name, version, seed, rating, lot}).

The plan of a running edition lives in it: rounds for the Swiss system ({round, bye, pairings
with board, white, black and match_id}), duels and bracket_size for knockout (knockout_bracket).
Each change of the plan, and each withdrawal, raises revision; a plan is written only if the
revision is still the one it was computed from. The games of a plan follow in a second step that
adds only those still missing and then sets scheduled, so a crash in between repeats it safely.
The end stores the final result in final ({table} or {placements}) and the winner.
"""

from datetime import datetime

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from sbm_store.names import EDITIONS

SCHEMA_VERSION = 1
PLANNED = "planned"
RUNNING = "running"
FINISHED = "finished"


def new_edition(
    tournament_id: ObjectId, number: int, *, starts_after: datetime | None, now: datetime
) -> dict:
    return {
        "_id": ObjectId(),
        "schema_version": SCHEMA_VERSION,
        "tournament_id": tournament_id,
        "number": number,
        "status": PLANNED,
        "starts_after": starts_after,
        "settings": None,
        "participants": [],
        "withdrawn": [],
        "revision": 0,
        "scheduled": False,
        "round": 0,
        "rounds": [],
        "duels": [],
        "bracket_size": None,
        "final": None,
        "winner": None,
        "created_at": now,
        "started_at": None,
        "finished_at": None,
    }


def insert(db: Database, edition: dict) -> bool:
    """False if the tournament has an edition with this number already."""
    try:
        db[EDITIONS].insert_one(edition)
    except DuplicateKeyError:
        return False
    return True


def get(db: Database, edition_id: ObjectId) -> dict | None:
    return db[EDITIONS].find_one({"_id": edition_id})


def of_tournament(db: Database, tournament_id: ObjectId) -> list[dict]:
    """All editions of a tournament, newest first."""
    return list(db[EDITIONS].find({"tournament_id": tournament_id}).sort("number", DESCENDING))


def latest(db: Database, tournament_id: ObjectId) -> dict | None:
    return db[EDITIONS].find_one({"tournament_id": tournament_id}, sort=[("number", DESCENDING)])


def latest_of(db: Database, tournament_ids: list[ObjectId]) -> dict[ObjectId, dict]:
    """The newest edition of each tournament."""
    found = db[EDITIONS].find({"tournament_id": {"$in": tournament_ids}}).sort("number", ASCENDING)
    return {edition["tournament_id"]: edition for edition in found}


def start_now(db: Database, tournament_id: ObjectId, now: datetime) -> bool:
    """Lets the planned edition start now (E171); False if none waits or it is due already."""
    result = db[EDITIONS].update_one(
        {
            "tournament_id": tournament_id,
            "status": PLANNED,
            "$or": [{"starts_after": None}, {"starts_after": {"$gt": now}}],
        },
        {"$set": {"starts_after": now}},
    )
    return result.modified_count == 1


def reschedule(db: Database, edition_id: ObjectId, starts_after: datetime | None) -> None:
    db[EDITIONS].update_one(
        {"_id": edition_id, "status": PLANNED}, {"$set": {"starts_after": starts_after}}
    )


def due(db: Database, now: datetime) -> list[dict]:
    query = {"status": PLANNED, "starts_after": {"$ne": None, "$lte": now}}
    return list(db[EDITIONS].find(query).sort([("starts_after", ASCENDING), ("_id", ASCENDING)]))


def begin(
    db: Database,
    edition_id: ObjectId,
    *,
    settings: dict,
    participants: list[dict],
    plan: dict,
    now: datetime,
) -> dict | None:
    """Starts a planned edition with its first plan; returns it as it is now, None if it is not
    planned (any more)."""
    result = db[EDITIONS].update_one(
        {"_id": edition_id, "status": PLANNED},
        {
            "$set": {
                "status": RUNNING,
                "settings": settings,
                "participants": participants,
                "scheduled": False,
                "started_at": now,
                **plan,
            },
            "$inc": {"revision": 1},
        },
    )
    return get(db, edition_id) if result.modified_count == 1 else None


def save_plan(db: Database, edition: dict, plan: dict) -> dict | None:
    """Writes a new plan computed from edition; None if the edition changed meanwhile."""
    result = db[EDITIONS].update_one(
        {"_id": edition["_id"], "status": RUNNING, "revision": edition["revision"]},
        {"$set": {**plan, "scheduled": False}, "$inc": {"revision": 1}},
    )
    return get(db, edition["_id"]) if result.modified_count == 1 else None


def mark_scheduled(db: Database, edition: dict) -> None:
    """Confirms that the games of the edition's plan exist; a newer plan stays unconfirmed."""
    db[EDITIONS].update_one(
        {"_id": edition["_id"], "revision": edition["revision"]}, {"$set": {"scheduled": True}}
    )


def running(db: Database) -> list[dict]:
    return list(db[EDITIONS].find({"status": RUNNING}).sort("_id", ASCENDING))


def running_with_bot(
    db: Database, bot_id: ObjectId, tournament_id: ObjectId | None = None
) -> list[dict]:
    query: dict = {"status": RUNNING, "participants.bot_id": bot_id}
    if tournament_id is not None:
        query["tournament_id"] = tournament_id
    return list(db[EDITIONS].find(query))


def add_withdrawn(db: Database, edition_id: ObjectId, bot_id: ObjectId) -> None:
    db[EDITIONS].update_one(
        {"_id": edition_id, "withdrawn": {"$ne": bot_id}},
        {"$push": {"withdrawn": bot_id}, "$inc": {"revision": 1}},
    )


def finish(
    db: Database, edition_id: ObjectId, *, final: dict, winner: dict | None, now: datetime
) -> bool:
    result = db[EDITIONS].update_one(
        {"_id": edition_id, "status": RUNNING},
        {"$set": {"status": FINISHED, "final": final, "winner": winner, "finished_at": now}},
    )
    return result.modified_count == 1


def participant(edition: dict, bot_id: ObjectId) -> dict | None:
    return next((entry for entry in edition["participants"] if entry["bot_id"] == bot_id), None)
