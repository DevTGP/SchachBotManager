"""Tournaments and their editions (E172, E173); leagues get a calendar instead of a pause (E171).

A league with pause_minutes gets the calendar first_start = now and interval_hours =
⌈pause_minutes / 60⌉, at least 1; pause_minutes leaves leagues and the settings of seasons.
"""

import math
from datetime import UTC, datetime

from pymongo import ASCENDING, IndexModel
from pymongo.database import Database

from sbm_store import recurrence
from sbm_store.names import EDITIONS, LEAGUES, MATCHES, SEASONS, TOURNAMENTS


def apply(db: Database) -> None:
    db[TOURNAMENTS].create_indexes([IndexModel([("name_key", ASCENDING)], unique=True)])
    db[EDITIONS].create_indexes(
        [
            IndexModel([("tournament_id", ASCENDING), ("number", ASCENDING)], unique=True),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("participants.bot_id", ASCENDING)]),
        ]
    )
    db[MATCHES].create_indexes(
        [IndexModel([("context.edition_id", ASCENDING), ("status", ASCENDING)], sparse=True)]
    )
    now = datetime.now(UTC)
    for league in db[LEAGUES].find({"pause_minutes": {"$exists": True}}):
        hours = max(recurrence.MIN_HOURS, math.ceil(league["pause_minutes"] / 60))
        calendar = recurrence.new_recurrence(now, min(hours, recurrence.MAX_HOURS))
        db[LEAGUES].update_one(
            {"_id": league["_id"]},
            {"$set": {"recurrence": calendar}, "$unset": {"pause_minutes": ""}},
        )
    db[LEAGUES].update_many({"recurrence": {"$exists": False}}, {"$set": {"recurrence": None}})
    db[SEASONS].update_many(
        {"settings.pause_minutes": {"$exists": True}}, {"$unset": {"settings.pause_minutes": ""}}
    )
