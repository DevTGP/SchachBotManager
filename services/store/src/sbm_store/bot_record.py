"""Wins, draws and losses of a bot per discipline (E141)."""

from dataclasses import dataclass

from bson import ObjectId
from pymongo.database import Database

from sbm_store.matches import FINISHED
from sbm_store.names import MATCHES

RESULTS = ["1-0", "0-1", "1/2-1/2"]


@dataclass(frozen=True)
class Counts:
    wins: int = 0
    draws: int = 0
    losses: int = 0

    @property
    def games(self) -> int:
        return self.wins + self.draws + self.losses

    def __add__(self, other: "Counts") -> "Counts":
        return Counts(self.wins + other.wins, self.draws + other.draws, self.losses + other.losses)


def by_discipline(db: Database, bot_id: ObjectId) -> dict[ObjectId | None, Counts]:
    """All finished games of the bot except those against itself, rated or not, against bots
    and people, forfeits included; None stands for free times without a stored discipline."""
    as_white = {"$eq": ["$white.bot_id", bot_id]}
    pipeline = [
        {
            "$match": {
                "status": FINISHED,
                "result": {"$in": RESULTS},
                "$or": [{"white.bot_id": bot_id}, {"black.bot_id": bot_id}],
                "$expr": {"$ne": ["$white.bot_id", "$black.bot_id"]},
            }
        },
        {
            "$project": {
                "discipline_id": {"$ifNull": ["$discipline_snapshot.discipline_id", None]},
                "won": {"$cond": [as_white, "1-0", "0-1"]},
                "result": 1,
            }
        },
        {
            "$group": {
                "_id": "$discipline_id",
                "games": {"$sum": 1},
                "wins": {"$sum": {"$cond": [{"$eq": ["$result", "$won"]}, 1, 0]}},
                "draws": {"$sum": {"$cond": [{"$eq": ["$result", "1/2-1/2"]}, 1, 0]}},
            }
        },
    ]
    return {
        group["_id"]: Counts(
            group["wins"], group["draws"], group["games"] - group["wins"] - group["draws"]
        )
        for group in db[MATCHES].aggregate(pipeline)
    }
