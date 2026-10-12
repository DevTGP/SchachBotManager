"""Moving running editions on (E174–E177); the runner calls this each round.

Per edition: lay out games a crash left missing, forfeit the waiting games of withdrawn bots,
give a round robin's next round its jobs (E187), take the format's next step and finish the
edition once it is done. A round robin edition is done when all its games have ended; the Swiss
system and knockout pair their next round first.
"""

import random
from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import (
    edition_end,
    edition_games,
    editions,
    knockout_duels,
    swiss_rounds,
    tournament_withdrawal,
    tournaments,
)


def advance_running(
    db: Database, now: datetime, rng: random.Random | None = None
) -> list[ObjectId]:
    """Moves each running edition on; returns the ids of those finished."""
    rng = rng or random.Random()
    finished = []
    for edition in editions.running(db):
        if not edition["scheduled"]:
            edition_games.lay_out(db, edition, now)
        tournament_withdrawal.sweep(db, edition, now)
        current = editions.get(db, edition["_id"])
        if current is None or current["status"] != editions.RUNNING:
            continue
        if current["scheduled"] and current["settings"]["format"] == tournaments.ROUND_ROBIN:
            edition_games.add_jobs(db, current, now)
        if _done(db, current, now, rng):
            edition_end.finish(db, current, now)
            finished.append(current["_id"])
    return finished


def _done(db: Database, edition: dict, now: datetime, rng: random.Random) -> bool:
    if not edition["scheduled"]:
        return False
    match edition["settings"]["format"]:
        case tournaments.SWISS:
            return swiss_rounds.advance(db, edition, now)
        case tournaments.KNOCKOUT:
            return knockout_duels.advance(db, edition, now, rng)
        case _:
            return not edition_games.open_games(db, edition["_id"])
