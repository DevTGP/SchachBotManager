"""Ratings of bots (E103): kept on the bot, counted from finished rated matches in order.

A counted match keeps in `rating` both sides' rating before and after it and a sequence number
`seq`, unique by migration 0006. A bot keeps its current `rating` (value, games, seq). Counting
takes two writes without a transaction: first the match claims the next number, then both bots
take their new values. A crash in between is repaired before the next match is counted: the
last counted match is applied again, which changes nothing if the bots already have it. Two
runners counting at once both claim the same number; the unique index lets only one win.
"""

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from sbm_store import bots
from sbm_store.matches import FINISHED
from sbm_store.names import BOTS, MATCHES
from sbm_store.rating_rule import START, white_gain

COLORS = ("white", "black")
PENDING = {"status": FINISHED, "rated": True, "rating": {"$exists": False}}
IN_ORDER = [("finished_at", ASCENDING), ("_id", ASCENDING)]


def current(bot: dict | None) -> dict:
    """value and games of a bot; a bot without rated matches stands at the start."""
    rating = (bot or {}).get("rating")
    if rating is None:
        return {"value": START, "games": 0}
    return {"value": rating["value"], "games": rating["games"]}


def count_pending(db: Database) -> int:
    """Counts the finished rated matches not counted yet, oldest first; returns how many."""
    counted = 0
    while True:
        seq = _settle_last(db) + 1
        match = db[MATCHES].find_one(PENDING, sort=IN_ORDER)
        if match is None:
            return counted
        if _count(db, match, seq):
            counted += 1


def ranking(db: Database) -> list[dict]:
    """Public bots with at least one counted match, highest rating first."""
    return list(
        db[BOTS]
        .find({"status": {"$in": list(bots.PUBLIC)}, "rating.games": {"$gte": 1}})
        .sort([("rating.value", DESCENDING), ("name_key", ASCENDING), ("version_no", ASCENDING)])
    )


def _settle_last(db: Database) -> int:
    """Applies the last counted match to its bots again; returns its number, 0 if none."""
    last = db[MATCHES].find_one({"rating.seq": {"$exists": True}}, sort=[("rating.seq", -1)])
    if last is None:
        return 0
    _apply(db, last)
    return last["rating"]["seq"]


def _count(db: Database, match: dict, seq: int) -> bool:
    """Claims seq for the match and moves both ratings; False if another runner came first."""
    white_id, black_id = (match[color]["bot_id"] for color in COLORS)
    if white_id == black_id:
        # A bot against itself cannot win or lose points (E103).
        db[MATCHES].update_one({"_id": match["_id"]}, {"$set": {"rated": False}})
        return False
    white, black = current(bots.get(db, white_id)), current(bots.get(db, black_id))
    gain = white_gain(white["value"], black["value"], match["result"])
    rating = {
        "seq": seq,
        "white": _side(white, gain),
        "black": _side(black, -gain),
    }
    try:
        claimed = db[MATCHES].update_one(
            {**PENDING, "_id": match["_id"]}, {"$set": {"rating": rating}}
        )
    except DuplicateKeyError:
        return False
    if claimed.modified_count != 1:
        return False
    _apply(db, match | {"rating": rating})
    return True


def _side(before: dict, gain: int) -> dict:
    return {
        "before": before["value"],
        "after": before["value"] + gain,
        "games": before["games"] + 1,
    }


def _apply(db: Database, match: dict) -> None:
    seq = match["rating"]["seq"]
    for color in COLORS:
        side = match["rating"][color]
        db[BOTS].update_one(
            {
                "_id": match[color]["bot_id"],
                "$or": [{"rating": {"$exists": False}}, {"rating.seq": {"$lt": seq}}],
            },
            {"$set": {"rating": {"value": side["after"], "games": side["games"], "seq": seq}}},
        )
