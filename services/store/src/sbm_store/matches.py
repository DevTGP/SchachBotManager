"""The matches collection: one document per game, moves embedded (datenmodell.md).

Status: queued → running → finished, or aborted after repeated infrastructure errors. A match
that loses its runner goes back to queued and starts over.
"""

from datetime import datetime

from bson import ObjectId
from pymongo import DESCENDING
from pymongo.database import Database

from sbm_store.discipline import STANDARD_FEN, Discipline, is_rated
from sbm_store.names import MATCHES

SCHEMA_VERSION = 1
QUEUED = "queued"
RUNNING = "running"
FINISHED = "finished"
ABORTED = "aborted"
STATUSES = (QUEUED, RUNNING, FINISHED, ABORTED)
SINGLE = "single"
LEAGUE = "league"
# A league game not played because a bot withdrew (E136).
FORFEIT = "forfeit_withdrawn"

NEWEST_FIRST = [("created_at", DESCENDING), ("_id", DESCENDING)]
SUMMARY_FIELDS = (
    "type",
    "status",
    "white",
    "black",
    "discipline_snapshot",
    "rated",
    "rating",
    "queue",
    "result",
    "termination",
    "series",
    "context",
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
    rated: bool = True,
    series: dict | None = None,
    created_by: ObjectId | None = None,
    counted: bool = False,
) -> dict:
    """A queued single game between two bot documents; a bot against itself is never rated.

    rated=False keeps a game unrated that would count (E158). series places the game in a
    series (E155); created_by is the account that set it, counted whether its daily limit paid
    for it (E156). The optional fields are left out when unset, which keeps their indexes small.
    """
    match = {
        "_id": ObjectId(),
        "schema_version": SCHEMA_VERSION,
        "type": SINGLE,
        "discipline_snapshot": discipline.to_document(),
        "white": side(white),
        "black": side(black),
        "status": QUEUED,
        "queue": {"priority": priority},
        "rated": rated and is_rated(discipline, start_fen) and white["_id"] != black["_id"],
        "start_fen": start_fen,
        "moves": [],
        "result": None,
        "termination": None,
        "termination_detail": None,
        "created_at": now,
        "started_at": None,
        "finished_at": None,
    }
    if series is not None:
        match["series"] = series
    if created_by is not None:
        match["created_by"] = created_by
    if counted:
        match["counted"] = True
    return match


def new_league_match(
    white: dict, black: dict, discipline: Discipline, *, context: dict, priority: int, now: datetime
) -> dict:
    """A queued league game from the standard position (E134); context places it.

    white and black are bot documents or season entries with _id, name and version.
    """
    match = new_match(white, black, discipline, start_fen=STANDARD_FEN, priority=priority, now=now)
    match.update(type=LEAGUE, context=context)
    return match


def league_context(
    season: dict, league_name: str, *, tier: int, round_number: int, board: int
) -> dict:
    """Where a league game stands; tier, round and board count from 1."""
    return {
        "league_id": season["league_id"],
        "league_name": league_name,
        "season_id": season["_id"],
        "season_number": season["number"],
        "tier": tier,
        "round": round_number,
        "board": board,
    }


def series_place(series_id: ObjectId, index: int, games: int) -> dict:
    """Where a game stands in its series; index counts from 1 (E155)."""
    return {"id": series_id, "index": index, "games": games}


def insert(db: Database, match: dict) -> None:
    db[MATCHES].insert_one(match)


def get(db: Database, match_id: ObjectId) -> dict | None:
    return db[MATCHES].find_one({"_id": match_id})


def summaries(db: Database, match_ids: list[ObjectId]) -> dict[ObjectId, dict]:
    cursor = db[MATCHES].find({"_id": {"$in": match_ids}}, SUMMARY_PROJECTION)
    return {match["_id"]: match for match in cursor}


def of_series(db: Database, series_id: ObjectId) -> list[dict]:
    """The summaries of a series' games in their order (E155)."""
    cursor = db[MATCHES].find({"series.id": series_id}, SUMMARY_PROJECTION).sort("series.index")
    return list(cursor)


def match_filter(
    status: str | None = None,
    bot_id: ObjectId | None = None,
    *,
    opponent_id: ObjectId | None = None,
    discipline_id: ObjectId | None = None,
    created_by: ObjectId | None = None,
    season_id: ObjectId | None = None,
    tier: int | None = None,
) -> dict:
    """opponent_id narrows the games of bot_id to those against that bot (E156); tier the games
    of season_id to one tier (E137)."""
    query: dict = {}
    if status is not None:
        query["status"] = status
    if bot_id is not None and opponent_id is not None:
        query["$or"] = [
            {"white.bot_id": bot_id, "black.bot_id": opponent_id},
            {"white.bot_id": opponent_id, "black.bot_id": bot_id},
        ]
    elif bot_id is not None:
        query["$or"] = [{"white.bot_id": bot_id}, {"black.bot_id": bot_id}]
    if discipline_id is not None:
        query["discipline_snapshot.discipline_id"] = discipline_id
    if created_by is not None:
        query["created_by"] = created_by
    if season_id is not None:
        query["context.season_id"] = season_id
        if tier is not None:
            query["context.tier"] = tier
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


def abort(db: Database, match_id: ObjectId, detail: str, now: datetime) -> bool:
    """Gives up a match that failed for infrastructure reasons too often, or that an admin
    cancelled (E152); it does not count. False if the match had ended already."""
    result = db[MATCHES].update_one(
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
    return result.modified_count == 1


def forfeit(db: Database, match: dict, loser_id: ObjectId, now: datetime) -> bool:
    """Ends a waiting league game unplayed: the opponent of loser_id wins, unrated (E136).

    False if the match is no longer queued, e.g. because a runner started it.
    """
    result = "0-1" if match["white"]["bot_id"] == loser_id else "1-0"
    updated = db[MATCHES].update_one(
        {"_id": match["_id"], "status": QUEUED},
        {
            "$set": {
                "status": FINISHED,
                "rated": False,
                "result": result,
                "termination": FORFEIT,
                "termination_detail": "the opponent withdrew from the league",
                "finished_at": now,
            }
        },
    )
    return updated.modified_count == 1


def set_priority(db: Database, match_id: ObjectId, priority: int) -> None:
    """Mirrors the priority of the match's job (E152)."""
    db[MATCHES].update_one({"_id": match_id}, {"$set": {"queue.priority": priority}})


def recent_durations_ms(db: Database, discipline_name: str, limit: int) -> list[int]:
    """Durations of the latest finished matches of a discipline, newest first."""
    cursor = (
        db[MATCHES]
        .find(
            {
                "status": FINISHED,
                "discipline_snapshot.name": discipline_name,
                "started_at": {"$ne": None},
                # Interactive games bypass the queue and say nothing about its times.
                "type": {"$nin": ["human", "remote"]},
            },
            {"started_at": 1, "finished_at": 1},
        )
        .sort("finished_at", DESCENDING)
        .limit(limit)
    )
    return [
        int((match["finished_at"] - match["started_at"]).total_seconds() * 1000) for match in cursor
    ]
