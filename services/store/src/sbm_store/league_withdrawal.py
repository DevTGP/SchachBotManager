"""A bot or an account leaving its leagues (E136, E17, E182).

Leaving ends the active registrations. In a running season the participant counts as
withdrawn: its waiting games end unplayed as forfeit wins of the opponents, a game already
running is played to the end and counts. The runner sweeps the withdrawn participants of
running seasons each round, so a crash in between leaves no waiting game behind.
"""

from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import jobs, matches, registrations, seasons
from sbm_store.names import MATCHES


def withdraw(
    db: Database,
    participant: ObjectId,
    reason: str,
    now: datetime,
    *,
    league_id: ObjectId | None = None,
) -> int:
    """Takes the bot or account out of all its leagues, or only league_id; returns the games
    forfeited."""
    registrations.leave(db, participant, reason, now, target_id=league_id)
    forfeited = 0
    for season in seasons.running_with_bot(db, participant, league_id):
        seasons.add_withdrawn(db, season["_id"], participant)
        forfeited += forfeit_waiting(db, season["_id"], participant, now)
    return forfeited


def forfeit_waiting(db: Database, season_id: ObjectId, participant: ObjectId, now: datetime) -> int:
    """Ends the participant's waiting games of a season as forfeits; returns how many."""
    query = matches.match_filter(
        status=matches.QUEUED, participant=participant, season_id=season_id
    )
    forfeited = 0
    for match in db[MATCHES].find(query, {"white": 1, "black": 1}):
        # The match goes first: a runner that took the job already finds it ended.
        forfeited += matches.forfeit(db, match, participant, now)
        jobs.cancel_match(db, match["_id"], now, running=False)
    return forfeited


def sweep(db: Database, now: datetime) -> int:
    """Forfeits the waiting games of withdrawn participants in running seasons; returns how many."""
    forfeited = 0
    for season in seasons.running(db):
        for participant in season["withdrawn"]:
            forfeited += forfeit_waiting(db, season["_id"], participant, now)
    return forfeited
