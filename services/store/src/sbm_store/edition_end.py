"""Finishing an edition (E177, E171).

The next edition waits for the first date of the calendar after the start of this one, which may
have passed already; without a calendar it waits for an admin. It is stored before this one is
marked finished: a crash in between finishes this one again, and the unique number stops a second
copy of the next.
"""

from datetime import datetime

from pymongo.database import Database

from sbm_store import edition_tables, editions, recurrence, tournaments


def finish(db: Database, edition: dict, now: datetime) -> None:
    final, winner = edition_tables.final(db, edition)
    tournament = tournaments.get(db, edition["tournament_id"])
    calendar = tournament.get("recurrence") if tournament is not None else None
    starts_after = recurrence.next_slot(calendar, edition["started_at"])
    following = editions.new_edition(
        edition["tournament_id"], edition["number"] + 1, starts_after=starts_after, now=now
    )
    editions.insert(db, following)
    editions.finish(db, edition["_id"], final=final, winner=winner, now=now)
