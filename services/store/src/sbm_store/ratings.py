"""Ratings of bots and accounts (E103, E117): kept on the bot or the user per discipline (E163),
counted from finished rated matches in order.

A counted match keeps in `rating` both sides' rating in its discipline before and after it and a
sequence number `seq`, unique by migration 0006. A side is a bot (bot_id) or a person with an
account (user_id); either keeps its current rating per discipline in `ratings` (rating_values)
on its own document. Counting takes two writes without a transaction: first the match claims the
next number, then both sides take their new values. A crash in between is repaired before the
next match is counted: the last counted match is applied again, which changes nothing if both
sides already have it. Two runners counting at once both claim the same number; the unique index
lets only one win.
"""

from bson import ObjectId
from pymongo import ASCENDING
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from sbm_store import bots, rating_settings, rating_values, users
from sbm_store.matches import FINISHED
from sbm_store.names import BOTS, MATCHES, USERS
from sbm_store.rating_rule import RatingRule, white_gain

COLORS = ("white", "black")
PENDING = {"status": FINISHED, "rated": True, "rating": {"$exists": False}}
IN_ORDER = [("finished_at", ASCENDING), ("_id", ASCENDING)]


def count_pending(db: Database) -> int:
    """Counts the finished rated matches not counted yet, oldest first; returns how many."""
    rule = rating_settings.get(db)
    counted = 0
    while True:
        seq = _settle_last(db) + 1
        match = db[MATCHES].find_one(PENDING, sort=IN_ORDER)
        if match is None:
            return counted
        if _count(db, match, seq, rule):
            counted += 1


def _settle_last(db: Database) -> int:
    """Applies the last counted match to its bots again; returns its number, 0 if none."""
    last = db[MATCHES].find_one({"rating.seq": {"$exists": True}}, sort=[("rating.seq", -1)])
    if last is None:
        return 0
    _apply(db, last)
    return last["rating"]["seq"]


def _count(db: Database, match: dict, seq: int, rule: RatingRule) -> bool:
    """Claims seq for the match and moves both ratings; False if another runner came first."""
    white_holder, black_holder = (holder(match[color]) for color in COLORS)
    discipline_id = discipline_of(match)
    if white_holder == black_holder or None in (white_holder, black_holder, discipline_id):
        # A bot against itself cannot win or lose points (E103); a guest has no rating; rated
        # matches always have a stored discipline (E100), so a missing one is a broken match.
        db[MATCHES].update_one({"_id": match["_id"]}, {"$set": {"rated": False}})
        return False
    white, black = (
        rating_values.in_discipline(_load(db, side), discipline_id, rule.start)
        for side in (white_holder, black_holder)
    )
    gain = white_gain(white["value"], black["value"], match["result"], rule)
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


def discipline_of(match: dict) -> ObjectId | None:
    return match["discipline_snapshot"].get("discipline_id")


def holder(side: dict) -> tuple[str, ObjectId] | None:
    """Where a side keeps its rating: the bot, or the account of a person; None for a guest."""
    if side.get("bot_id") is not None:
        return BOTS, side["bot_id"]
    if side.get("kind") == "human" and side.get("user_id") is not None:
        return USERS, side["user_id"]
    return None


def _load(db: Database, side: tuple[str, ObjectId]) -> dict | None:
    collection, holder_id = side
    return bots.get(db, holder_id) if collection == BOTS else users.get(db, holder_id)


def _apply(db: Database, match: dict) -> None:
    seq = match["rating"]["seq"]
    path = f"{rating_values.FIELD}.{rating_values.key(discipline_of(match))}"
    for color in COLORS:
        side = match["rating"][color]
        place = holder(match[color])
        if place is None:
            continue
        collection, holder_id = place
        db[collection].update_one(
            {
                "_id": holder_id,
                "$or": [{path: {"$exists": False}}, {f"{path}.seq": {"$lt": seq}}],
            },
            {"$set": {path: {"value": side["after"], "games": side["games"], "seq": seq}}},
        )
