"""Interactive matches: a bot against a person in the browser or a bot on the person's machine
(M7, E111, E113).

They bypass the queue (E24): their job has the type play, which only the play runner takes.
A game of a person with an account counts for the ratings (E103, E117). Each side that is not
a bot holds a seat: a secret token the web API hands out once; the match keeps only its hash,
which the runner gives to the gateway.
"""

from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import jobs, matches, tokens
from sbm_store.discipline import Discipline, is_rated
from sbm_store.names import JOBS, MATCHES

PLAY_JOB = "play"
HUMAN = "human"
REMOTE = "remote"
MATCH_TYPES = (HUMAN, REMOTE)
SEAT_KINDS = (HUMAN, REMOTE)
COLORS = ("white", "black")


def new_seat() -> tuple[str, str]:
    """A seat token and its hash; only the hash is stored."""
    token = tokens.new_token()
    return token, tokens.token_hash(token)


def seat_side(kind: str, name: str, *, user_id: ObjectId | None, seat_hash: str) -> dict:
    """A person or a remote bot as a side; user_id is None for a guest."""
    if kind not in SEAT_KINDS:
        raise ValueError(f"unknown seat kind {kind!r}")
    return {
        "kind": kind,
        "bot_id": None,
        "user_id": user_id,
        "name": name,
        "version": None,
        "sdk": None,
        "lang": None,
        "seat_hash": seat_hash,
    }


def is_seat(side: dict) -> bool:
    return side["kind"] in SEAT_KINDS


def origin(*, ip_key: str | None, user_id: ObjectId | None, token_id: ObjectId | None) -> dict:
    """Who asked for the game, for the limits per address, account and token (E115).

    ip_key is a hash of the address; the address itself is not stored.
    """
    return {"ip_key": ip_key, "user_id": user_id, "token_id": token_id}


def rated(
    match_type: str, sides: tuple[dict, dict], discipline: Discipline, start_fen: str
) -> bool:
    """A person with an account against a bot, with a discipline from the start position (E103).

    Guests and remote bots are never rated: a guest has no rating, a remote bot is not verified.
    """
    if match_type != HUMAN or not is_rated(discipline, start_fen):
        return False
    return any(side["kind"] == HUMAN and side["user_id"] is not None for side in sides)


def new_play_match(
    match_type: str,
    white: dict,
    black: dict,
    discipline: Discipline,
    *,
    start_fen: str,
    now: datetime,
    requested_by: dict | None = None,
) -> dict:
    """white and black are sides: matches.side(bot) or seat_side(...); requested_by is an
    origin(...).
    """
    if match_type not in MATCH_TYPES:
        raise ValueError(f"unknown interactive match type {match_type!r}")
    if not any(is_seat(side) for side in (white, black)):
        raise ValueError("an interactive match needs a seat")
    return {
        "_id": ObjectId(),
        "schema_version": matches.SCHEMA_VERSION,
        "type": match_type,
        "discipline_snapshot": discipline.to_document(),
        "white": white,
        "black": black,
        "status": matches.QUEUED,
        "queue": None,
        "rated": rated(match_type, (white, black), discipline, start_fen),
        "start_fen": start_fen,
        "moves": [],
        "result": None,
        "termination": None,
        "termination_detail": None,
        "created_at": now,
        "started_at": None,
        "finished_at": None,
        "origin": requested_by or origin(ip_key=None, user_id=None, token_id=None),
    }


def new_play_job(match_id: ObjectId, *, now: datetime) -> dict:
    job = jobs.new_match_job(match_id, priority=0, now=now)
    job["type"] = PLAY_JOB
    return job


def create(
    db: Database,
    match_type: str,
    white: dict,
    black: dict,
    discipline: Discipline,
    *,
    start_fen: str,
    now: datetime,
    requested_by: dict | None = None,
) -> ObjectId:
    """Stores the match and its play job; the match id is returned.

    Without transactions a crash in between leaves a queued match without a job; the play
    runner never starts it.
    """
    match = new_play_match(
        match_type,
        white,
        black,
        discipline,
        start_fen=start_fen,
        now=now,
        requested_by=requested_by,
    )
    matches.insert(db, match)
    jobs.insert(db, new_play_job(match["_id"], now=now))
    return match["_id"]


def active_by(db: Database, field: str, value: object) -> int:
    """Interactive games not yet over that this address, account or token asked for."""
    if field not in ("ip_key", "user_id", "token_id"):
        raise ValueError(f"unknown origin field {field!r}")
    return db[MATCHES].count_documents(
        {
            f"origin.{field}": value,
            "type": {"$in": list(MATCH_TYPES)},
            "status": {"$in": [matches.QUEUED, matches.RUNNING]},
        }
    )


def active_count(db: Database) -> int:
    """Interactive games waiting for or held by the play runner."""
    return db[JOBS].count_documents(
        {"type": PLAY_JOB, "status": {"$in": [jobs.QUEUED, jobs.RUNNING]}}
    )


def running_summaries(db: Database) -> list[dict]:
    """Interactive games under way as list summaries, earliest start first (E119)."""
    return list(
        db[MATCHES]
        .find(
            {"type": {"$in": list(MATCH_TYPES)}, "status": matches.RUNNING},
            matches.SUMMARY_PROJECTION,
        )
        .sort([("started_at", 1), ("_id", 1)])
    )
