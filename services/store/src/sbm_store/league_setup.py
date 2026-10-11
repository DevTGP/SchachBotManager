"""Creating a league with its first season and releasing that season (E131, E132)."""

from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import leagues, seasons


def create(db: Database, league: dict, now: datetime) -> bool:
    """Stores the league and its first season, planned without a start; False if the name is
    taken."""
    if not leagues.insert(db, league):
        return False
    seasons.insert(db, seasons.new_season(league["_id"], 1, starts_after=None, seeds=[], now=now))
    return True


def release(db: Database, league_id: ObjectId, now: datetime) -> bool:
    """Lets the first season start once enough bots are registered; False if none waits."""
    if seasons.latest(db, league_id) is None:
        # A crash after the league was stored left it without its first season.
        first = seasons.new_season(league_id, 1, starts_after=now, seeds=[], now=now)
        return seasons.insert(db, first)
    return seasons.release(db, league_id, now)
