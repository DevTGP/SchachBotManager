"""The matches collection: one document per game, moves embedded (datenmodell.md).

Status: queued → running → finished, or aborted after repeated infrastructure errors. A match
that loses its runner goes back to queued and starts over.
"""

from datetime import datetime

from bson import ObjectId
from pymongo import DESCENDING
from pymongo.database import Database

from sbm_store.discipline import Discipline, is_rated
from sbm_store.names import MATCHES

SCHEMA_VERSION = 1
QUEUED = "queued"
RUNNING = "running"
FINISHED = "finished"
ABORTED = "aborted"
STATUSES = (QUEUED, RUNNING, FINISHED, ABORTED)

NEWEST_FIRST = [("created_at", DESCENDING), ("_id", DESCENDING)]
SUMMARY_FIELDS = (
    "type",
    "status",
    "white",
    "black",
    "discipline_snapshot",
    "rated",
    "queue",
    "result",
    "termination",
    "created_at",
    "started_at",
    "finished_at",
)
# Lists leave out the moves but report how many there are.
SUMMARY_PROJECTION = {field: 1 for field in SUMMARY_FIELDS} | {"ply_count": {"$size": "$moves"}}


def side(bot: dict) -> dict:
    """A bot as a side of a match; sdk and lang follow from its ready message."""
    return {
        "kind": "bot",
        "bot_id": bot["_id"],
        "name": bot["name"],
        "version": bot.get("version"),
        "sdk": None,
        "lang": None,
    }


def new_match(
    white: dict,
    black: dict,
    discipline: Discipline,
    *,
    start_fen: str,
    priority: int,
    now: datetime,
) -> dict:
    """A queued single game between two bot documents."""
    return {
        "_id": ObjectId(),
        "schema_version": SCHEMA_VERSION,
        "type": "single",
        "discipline_snapshot": discipline.to_document(),
        "white": side(white),
        "black": side(black),
        "status": QUEUED,
        "queue": {"priority": priority},
        "rated": is_rated(discipline, start_fen),
        "start_fen": start_fen,
        "moves": [],
        "result": None,
        "termination": None,
        "termination_detail": None,
        "created_at": now,
        "started_at": None,
        "finished_at": None,
    }


def insert(db: Database, match: dict) -> None:
    db[MATCHES].insert_one(match)


def get(db: Database, match_id: ObjectId) -> dict | None:
    return db[MATCHES].find_one({"_id": match_id})


def summaries(db: Database, match_ids: list[ObjectId]) -> dict[ObjectId, dict]:
    cursor = db[MATCHES].find({"_id": {"$in": match_ids}}, SUMMARY_PROJECTION)
    return {match["_id"]: match for match in cursor}


def match_filter(status: str | None = None, bot_id: ObjectId | None = None) -> dict:
    query: dict = {}
    if status is not None:
        query["status"] = status
    if bot_id is not None:
        query["$or"] = [{"white.bot_id": bot_id}, {"black.bot_id": bot_id}]
    return query


def page(db: Database, query: dict, *, limit: int, offset: int) -> tuple[list[dict], int]:
    """Summaries newest first, and how many matches the query matches in total."""
    collection = db[MATCHES]
    items = list(
        collection.find(query, SUMMARY_PROJECTION).sort(NEWEST_FIRST).skip(offset).limit(limit)
    )
    return items, collection.count_documents(query)


def start(db: Database, match_id: ObjectId, now: datetime) -> bool:
    """Marks a queued match as running; False if it is not queued (any more)."""
    result = db[MATCHES].update_one(
        {"_id": match_id, "status": QUEUED},
        {"$set": {"status": RUNNING, "started_at": now}},
    )
    return result.modified_count == 1


def append_move(db: Database, match_id: ObjectId, move: dict) -> None:
    db[MATCHES].update_one({"_id": match_id, "status": RUNNING}, {"$push": {"moves": move}})


def finish(
    db: Database,
    match_id: ObjectId,
    *,
    sides: dict[str, dict],
    result: str,
    termination: str,
    detail: str,
    now: datetime,
) -> None:
    """sides maps white and black to the fields that change, e.g. sdk and lang."""
    fields = {
        "status": FINISHED,
        "result": result,
        "termination": termination,
        "termination_detail": detail,
        "finished_at": now,
    }
    for color, values in sides.items():
        for key, value in values.items():
            fields[f"{color}.{key}"] = value
    db[MATCHES].update_one({"_id": match_id, "status": RUNNING}, {"$set": fields})


def requeue(db: Database, match_id: ObjectId) -> None:
    """Discards a game cut short by an infrastructure error; it starts over later."""
    db[MATCHES].update_one(
        {"_id": match_id, "status": {"$in": [QUEUED, RUNNING]}},
        {
            "$set": {
                "status": QUEUED,
                "moves": [],
                "started_at": None,
                "white.sdk": None,
                "white.lang": None,
                "black.sdk": None,
                "black.lang": None,
            }
        },
    )


def abort(db: Database, match_id: ObjectId, detail: str, now: datetime) -> None:
    """Gives up a match that failed for infrastructure reasons too often; it does not count."""
    db[MATCHES].update_one(
        {"_id": match_id, "status": {"$in": [QUEUED, RUNNING]}},
        {
            "$set": {
                "status": ABORTED,
                "result": "*",
                "termination": "aborted",
                "termination_detail": detail,
                "finished_at": now,
            }
        },
    )


def recent_durations_ms(db: Database, discipline_name: str, limit: int) -> list[int]:
    """Durations of the latest finished matches of a discipline, newest first."""
    cursor = (
        db[MATCHES]
        .find(
            {
                "status": FINISHED,
                "discipline_snapshot.name": discipline_name,
                "started_at": {"$ne": None},
            },
            {"started_at": 1, "finished_at": 1},
        )
        .sort("finished_at", DESCENDING)
        .limit(limit)
    )
    return [
        int((match["finished_at"] - match["started_at"]).total_seconds() * 1000) for match in cursor
    ]
