"""The rating of a bot before and after each counted match, per discipline (E140)."""

from dataclasses import dataclass
from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store.names import MATCHES
from sbm_store.ratings import discipline_of

PROJECTION = {
    "white.bot_id": 1,
    "rating": 1,
    "finished_at": 1,
    "discipline_snapshot.discipline_id": 1,
}


@dataclass(frozen=True)
class Point:
    match_id: ObjectId
    finished_at: datetime
    before: int
    after: int


def of_bot(db: Database, bot_id: ObjectId) -> dict[ObjectId, list[Point]]:
    """The counted matches of the bot by discipline, each list in the order of counting (E104).
    A bot never plays a counted match against itself (E103)."""
    query = {
        "rating": {"$exists": True},
        "$or": [{"white.bot_id": bot_id}, {"black.bot_id": bot_id}],
    }
    history: dict[ObjectId, list[Point]] = {}
    for match in db[MATCHES].find(query, PROJECTION).sort("rating.seq", 1):
        color = "white" if match["white"].get("bot_id") == bot_id else "black"
        side = match["rating"][color]
        point = Point(match["_id"], match["finished_at"], side["before"], side["after"])
        history.setdefault(discipline_of(match), []).append(point)
    return history
