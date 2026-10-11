"""Creating a league with its first season, starting a season by hand and following a new
calendar (E131, E132, E171)."""

from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import leagues, recurrence, seasons


def create(db: Database, league: dict, now: datetime) -> bool:
    """Stores the league and its first season, planned for the first date of the calendar from
    now on or, without one, for an admin; False if the name is taken."""
    if not leagues.insert(db, league):
        return False
    starts_after = recurrence.next_slot(league["recurrence"], now, inclusive=True)
    seasons.insert(
        db, seasons.new_season(league["_id"], 1, starts_after=starts_after, seeds=[], now=now)
    )
    return True


def start(db: Database, league_id: ObjectId, now: datetime) -> bool:
    """Lets the planned season start now; False if none waits or it is due already."""
    if seasons.latest(db, league_id) is None:
        # A crash after the league was stored left it without its first season.
        first = seasons.new_season(league_id, 1, starts_after=now, seeds=[], now=now)
        return seasons.insert(db, first)
    return seasons.start_now(db, league_id, now)


def follow_calendar(db: Database, league: dict, now: datetime) -> None:
    """Sets the start of the planned season anew after the league's calendar changed."""
    found = seasons.of_league(db, league["_id"])
    if not found or found[0]["status"] != seasons.PLANNED:
        return
    previous = found[1] if len(found) > 1 else None
    calendar = league.get("recurrence")
    if previous is None or previous["started_at"] is None:
        starts_after = recurrence.next_slot(calendar, now, inclusive=True)
    else:
        starts_after = recurrence.next_slot(calendar, previous["started_at"])
    seasons.reschedule(db, found[0]["_id"], starts_after)
