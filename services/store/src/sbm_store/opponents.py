"""The head-to-head record of a bot against each opponent bot (E161)."""

from bson import ObjectId
from pymongo.database import Database

from sbm_store.matches import FINISHED
from sbm_store.names import MATCHES

# Games against people, from outside or against itself say nothing about a pairing of bots.
EXCLUDED_TYPES = ["human", "remote"]


def records(db: Database, bot_id: ObjectId) -> list[dict]:
    """One entry per opponent bot with games, wins, draws and losses from the bot's view, rated
    and unrated alike; most games first. Name and version come from the latest game."""
    as_white = {"$eq": ["$white.bot_id", bot_id]}
    pipeline = [
        {
            "$match": {
                "status": FINISHED,
                "type": {"$nin": EXCLUDED_TYPES},
                "$or": [{"white.bot_id": bot_id}, {"black.bot_id": bot_id}],
                "$expr": {"$ne": ["$white.bot_id", "$black.bot_id"]},
            }
        },
        {"$sort": {"finished_at": -1, "_id": -1}},
        {
            "$project": {
                "opponent": {"$cond": [as_white, "$black", "$white"]},
                "won": {"$cond": [as_white, "1-0", "0-1"]},
                "lost": {"$cond": [as_white, "0-1", "1-0"]},
                "result": 1,
            }
        },
        {
            "$group": {
                "_id": "$opponent.bot_id",
                "name": {"$first": "$opponent.name"},
                "version": {"$first": "$opponent.version"},
                "games": {"$sum": 1},
                "wins": {"$sum": {"$cond": [{"$eq": ["$result", "$won"]}, 1, 0]}},
                "draws": {"$sum": {"$cond": [{"$eq": ["$result", "1/2-1/2"]}, 1, 0]}},
                "losses": {"$sum": {"$cond": [{"$eq": ["$result", "$lost"]}, 1, 0]}},
            }
        },
        {"$sort": {"games": -1, "name": 1, "_id": 1}},
    ]
    return list(db[MATCHES].aggregate(pipeline))
