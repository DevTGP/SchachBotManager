"""The rankings of bots (E103) and of players (E118), overall or in one discipline (E163).

Each entry is a holder with its rating in the ranking. The overall rating is computed on read,
so both rankings sort in Python; there are few holders with rated games.
"""

from bson import ObjectId
from pymongo.database import Database

from sbm_store import bots, rating_values
from sbm_store.names import BOTS, USERS


def bot_ranking(db: Database, discipline_id: ObjectId | None, start: int) -> list[tuple]:
    """Public bots with at least one counted match, highest rating first, then name and version."""
    query = {"status": {"$in": list(bots.PUBLIC)}, **_played(discipline_id)}
    entries = [(bot, _rating(bot, discipline_id, start)) for bot in db[BOTS].find(query)]
    return sorted(entries, key=lambda entry: (-entry[1]["value"], *_bot_order(entry[0])))


def player_ranking(db: Database, discipline_id: ObjectId | None, start: int) -> list[tuple]:
    """Active accounts with at least one counted game against bots, highest rating first."""
    query = {"active": True, **_played(discipline_id)}
    entries = [(user, _rating(user, discipline_id, start)) for user in db[USERS].find(query)]
    return sorted(entries, key=lambda entry: (-entry[1]["value"], entry[0]["username_key"]))


def _bot_order(bot: dict) -> tuple:
    return bot["name_key"], bot["version_no"]


def _played(discipline_id: ObjectId | None) -> dict:
    if discipline_id is None:
        # Entries only come with a counted match, so any entry means at least one game.
        return {rating_values.FIELD: {"$exists": True, "$ne": {}}}
    return {f"{rating_values.FIELD}.{rating_values.key(discipline_id)}.games": {"$gte": 1}}


def _rating(holder: dict, discipline_id: ObjectId | None, start: int) -> dict:
    if discipline_id is None:
        return rating_values.overall(holder, start)
    return rating_values.in_discipline(holder, discipline_id, start)
