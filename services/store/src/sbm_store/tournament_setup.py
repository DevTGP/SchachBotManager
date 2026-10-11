"""Creating a tournament with its first edition, starting an edition by hand and following a new
calendar (E171, E172)."""

from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import editions, recurrence, tournaments


def create(db: Database, tournament: dict, now: datetime) -> bool:
    """Stores the tournament and its first edition, planned for the first date of the calendar
    from now on or, without one, for an admin; False if the name is taken."""
    if not tournaments.insert(db, tournament):
        return False
    starts_after = recurrence.next_slot(tournament["recurrence"], now, inclusive=True)
    editions.insert(
        db, editions.new_edition(tournament["_id"], 1, starts_after=starts_after, now=now)
    )
    return True


def start(db: Database, tournament_id: ObjectId, now: datetime) -> bool:
    """Lets the planned edition start now; False if none waits or it is due already."""
    if editions.latest(db, tournament_id) is None:
        # A crash after the tournament was stored left it without its first edition.
        return editions.insert(
            db, editions.new_edition(tournament_id, 1, starts_after=now, now=now)
        )
    return editions.start_now(db, tournament_id, now)


def follow_calendar(db: Database, tournament: dict, now: datetime) -> None:
    """Sets the start of the planned edition anew after the tournament's calendar changed."""
    found = editions.of_tournament(db, tournament["_id"])
    if not found or found[0]["status"] != editions.PLANNED:
        return
    previous = found[1] if len(found) > 1 else None
    calendar = tournament.get("recurrence")
    if previous is None or previous["started_at"] is None:
        starts_after = recurrence.next_slot(calendar, now, inclusive=True)
    else:
        starts_after = recurrence.next_slot(calendar, previous["started_at"])
    editions.reschedule(db, found[0]["_id"], starts_after)
