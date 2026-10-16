"""Releasing league and tournament games with an account and starting them on readiness
(E183–E185); the runner of the role match calls release, start_ready and expire each round.

A game with an account gets no job when its season or edition lays it out. release hands out
the waiting ones in the order (tier,) round, board, game, as long as no account in them holds
another released game that has not ended and, in a league or round robin, the game's round has
come (E189). The released game carries readiness: released_at,
deadline, started_at and per side {ready_at, seen_at}, None for a bot. The account says it is
ready with mark_ready, which its page repeats; once every account is ready and present, or at
the deadline every account is ready, the game gets a play job. An account not ready at the
deadline loses unplayed (forfeit_absent), both accounts absent give 0-0. reset puts a game back
after an infrastructure failure of the play runner: released anew, readiness and seats cleared.
"""

from datetime import datetime, timedelta

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.database import Database

from sbm_store import competition_pace, jobs, matches, participants, play
from sbm_store.names import EDITIONS, JOBS, MATCHES, SEASONS

DEFAULT_READY_HOURS = 48
# An account counts as present if its page reported within this time; the page reports every
# 15 seconds.
PRESENT = timedelta(seconds=45)
ABSENT_DETAIL = "not ready by the deadline"
COMPETITIONS = (matches.LEAGUE, matches.TOURNAMENT)
WITH_ACCOUNT = {"$or": [{"white.kind": play.HUMAN}, {"black.kind": play.HUMAN}]}
ORDER = [
    ("context.tier", 1),
    ("context.round", 1),
    ("context.board", 1),
    ("context.game", 1),
    ("_id", 1),
]


def release(db: Database, now: datetime) -> list[ObjectId]:
    """Releases the next waiting games with an account; returns their ids."""
    busy = _busy_accounts(db)
    hours: dict[ObjectId, int] = {}
    rounds: dict[tuple, int | None] = {}
    released = []
    query = {
        "type": {"$in": list(COMPETITIONS)},
        "status": matches.QUEUED,
        "readiness": None,
    } | WITH_ACCOUNT
    for match in db[MATCHES].find(query, {"white": 1, "black": 1, "context": 1}).sort(ORDER):
        if not competition_pace.due(db, match["context"], rounds):
            continue
        accounts = _accounts(match)
        blocked = bool(accounts & busy)
        # The games of an account come in order: a later one waits for this one as well.
        busy |= accounts
        if blocked:
            continue
        ready_hours = _ready_hours(db, match["context"], hours)
        readiness = new_readiness(match, now, ready_hours)
        updated = db[MATCHES].update_one(
            {"_id": match["_id"], "status": matches.QUEUED, "readiness": None},
            {"$set": {"readiness": readiness}},
        )
        if updated.modified_count == 1:
            released.append(match["_id"])
    return released


def new_readiness(match: dict, now: datetime, ready_hours: float) -> dict:
    return {
        "released_at": now,
        "deadline": now + timedelta(hours=ready_hours),
        "started_at": None,
        **{
            color: {"ready_at": None, "seen_at": None}
            if participants.is_human(match[color])
            else None
            for color in participants.COLORS
        },
    }


def color_of(match: dict, user_id: ObjectId) -> str | None:
    """The colour the account plays in the match, None if it plays none."""
    for color in participants.COLORS:
        side = match[color]
        if participants.is_human(side) and side["user_id"] == user_id:
            return color
    return None


def waiting_for_ready(match: dict) -> bool:
    """Whether the match is released and not started, so readiness may still be declared."""
    readiness = match.get("readiness")
    return (
        match["status"] == matches.QUEUED
        and readiness is not None
        and readiness["started_at"] is None
    )


def mark_ready(
    db: Database, match_id: ObjectId, color: str, seat_hash: str, now: datetime
) -> dict | None:
    """Marks the side ready (which stays) and present, with the hash of its seat; the match
    after the change, None if it is no longer waiting for readiness."""
    side = f"readiness.{color}"
    return db[MATCHES].find_one_and_update(
        {
            "_id": match_id,
            "status": matches.QUEUED,
            "readiness.started_at": None,
            side: {"$ne": None},
        },
        [
            {
                "$set": {
                    f"{side}.ready_at": {"$ifNull": [f"${side}.ready_at", now]},
                    f"{side}.seen_at": now,
                    f"{color}.seat_hash": {"$literal": seat_hash},
                }
            }
        ],
        return_document=ReturnDocument.AFTER,
    )


def present(side: dict | None, now: datetime) -> bool:
    return side is not None and side["seen_at"] is not None and now - side["seen_at"] <= PRESENT


def side_state(side: dict | None, now: datetime) -> dict | None:
    """ready and present of a side as the API shows them; None for a bot."""
    if side is None:
        return None
    return {"ready": side["ready_at"] is not None, "present": present(side, now)}


def startable(readiness: dict, now: datetime) -> bool:
    """Whether the next round of the runner starts the game: every account is ready and
    present, or ready at the deadline."""
    sides = _human_sides(readiness)
    if not all(side["ready_at"] is not None for side in sides):
        return False
    return readiness["deadline"] <= now or all(present(side, now) for side in sides)


def start_ready(db: Database, now: datetime) -> list[ObjectId]:
    """Starts each released game whose accounts are all ready and present, or all ready at the
    deadline, and gives each started game without an open play job one; returns the ids of the
    games started now."""
    started = []
    query = {
        "status": matches.QUEUED,
        "readiness.started_at": None,
        "readiness.deadline": {"$exists": True},
    }
    for match in db[MATCHES].find(query, {"readiness": 1}):
        if not startable(match["readiness"], now):
            continue
        updated = db[MATCHES].update_one(
            {"_id": match["_id"], "status": matches.QUEUED, "readiness.started_at": None},
            {"$set": {"readiness.started_at": now}},
        )
        if updated.modified_count == 1:
            started.append(match["_id"])
    _add_play_jobs(db, now)
    return started


def expire(db: Database, now: datetime) -> list[ObjectId]:
    """Ends each released game past its deadline in which an account is not ready: that side
    loses unplayed and unrated, 0-0 if both are accounts that were not ready; returns their ids."""
    ended = []
    query = {
        "status": matches.QUEUED,
        "readiness.started_at": None,
        "readiness.deadline": {"$lte": now},
    }
    for match in db[MATCHES].find(query, {"readiness": 1}):
        readiness = match["readiness"]
        absent = {
            color
            for color in participants.COLORS
            if readiness[color] is not None and readiness[color]["ready_at"] is None
        }
        if not absent:
            continue
        if absent == set(participants.COLORS):
            result = "0-0"
        else:
            result = "0-1" if "white" in absent else "1-0"
        updated = db[MATCHES].update_one(
            {"_id": match["_id"], "status": matches.QUEUED, "readiness.started_at": None},
            {
                "$set": {
                    "status": matches.FINISHED,
                    "rated": False,
                    "result": result,
                    "termination": matches.FORFEIT_ABSENT,
                    "termination_detail": ABSENT_DETAIL,
                    "finished_at": now,
                }
            },
        )
        if updated.modified_count == 1:
            ended.append(match["_id"])
    return ended


def reset(db: Database, match_id: ObjectId, now: datetime) -> bool:
    """Puts a competition game with an account back after an infrastructure failure (E185): it
    waits again, without moves, released anew with the same time to the deadline, nobody ready
    and no seats. False if it is no game with readiness or has ended. A second reset at the
    same instant, as when the play runner stops while the game gives up, changes nothing and
    still counts, so the caller does not abort the game instead."""
    match = db[MATCHES].find_one(
        {"_id": match_id, "status": {"$in": [matches.QUEUED, matches.RUNNING]}},
        {"readiness": 1, "white": 1, "black": 1},
    )
    if match is None or match.get("readiness") is None:
        return False
    readiness = match["readiness"]
    hours = (readiness["deadline"] - readiness["released_at"]) / timedelta(hours=1)
    fields = {
        "status": matches.QUEUED,
        "moves": [],
        "started_at": None,
        "readiness": new_readiness(match, now, hours),
    }
    for color in participants.COLORS:
        fields[f"{color}.sdk"] = None
        fields[f"{color}.lang"] = None
        if participants.is_human(match[color]):
            fields[f"{color}.seat_hash"] = None
    updated = db[MATCHES].update_one(
        {"_id": match_id, "status": {"$in": [matches.QUEUED, matches.RUNNING]}},
        {"$set": fields},
    )
    return updated.matched_count == 1


# The play jobs of competition games (E185).
COMPETITION_JOBS = {"payload.competition": True}


def is_competition(match: dict) -> bool:
    """Whether a match of the play runner is a league or tournament game (E185)."""
    return match.get("type") in COMPETITIONS


def _add_play_jobs(db: Database, now: datetime) -> None:
    """A play job for each started game that has none open; a crash between the start and the
    job leaves one without."""
    waiting = list(
        db[MATCHES].distinct(
            "_id", {"status": matches.QUEUED, "readiness.started_at": {"$ne": None}}
        )
    )
    if not waiting:
        return
    with_job = set(
        db[JOBS].distinct(
            "payload.match_id",
            {
                "type": jobs.PLAY,
                "payload.match_id": {"$in": waiting},
                "status": {"$in": [jobs.QUEUED, jobs.RUNNING]},
            },
        )
    )
    new = [_play_job(match_id, now) for match_id in waiting if match_id not in with_job]
    if new:
        db[JOBS].insert_many(new)


def _play_job(match_id: ObjectId, now: datetime) -> dict:
    """Marked, so the play runner takes it beyond the limits of E115 (E185)."""
    job = play.new_play_job(match_id, now=now)
    job["payload"]["competition"] = True
    return job


def _busy_accounts(db: Database) -> set[ObjectId]:
    """The accounts with a released competition game that has not ended."""
    busy: set[ObjectId] = set()
    query = {
        "type": {"$in": list(COMPETITIONS)},
        "status": {"$in": [matches.QUEUED, matches.RUNNING]},
        "readiness": {"$ne": None},
    }
    for match in db[MATCHES].find(query, {"white": 1, "black": 1}):
        busy |= _accounts(match)
    return busy


def _accounts(match: dict) -> set[ObjectId]:
    return {
        match[color]["user_id"]
        for color in participants.COLORS
        if participants.is_human(match[color])
    }


def _human_sides(readiness: dict) -> list[dict]:
    return [readiness[color] for color in participants.COLORS if readiness[color] is not None]


def _ready_hours(db: Database, context: dict, cache: dict) -> int:
    """The ready_hours of the game's season or edition; older snapshots have the default."""
    if "season_id" in context:
        collection, competition_id = SEASONS, context["season_id"]
    else:
        collection, competition_id = EDITIONS, context["edition_id"]
    if competition_id not in cache:
        found = db[collection].find_one({"_id": competition_id}, {"settings.ready_hours": 1})
        settings = (found or {}).get("settings") or {}
        cache[competition_id] = settings.get("ready_hours", DEFAULT_READY_HOURS)
    return cache[competition_id]
