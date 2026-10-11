"""A bot leaving its leagues (E136, E17).

Leaving ends the active registrations. In a running season the bot counts as withdrawn: its
waiting games end unplayed as forfeit wins of the opponents, a game already running is played
to the end and counts. The runner sweeps the withdrawn bots of running seasons each round, so a
crash in between leaves no waiting game behind.
"""

from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import jobs, matches, registrations, seasons
from sbm_store.names import MATCHES


def withdraw(
    db: Database,
    bot_id: ObjectId,
    reason: str,
    now: datetime,
    *,
    league_id: ObjectId | None = None,
) -> int:
    """Takes the bot out of all its leagues, or only league_id; returns the games forfeited."""
    registrations.leave(db, bot_id, reason, now, league_id=league_id)
    forfeited = 0
    for season in seasons.running_with_bot(db, bot_id, league_id):
        seasons.add_withdrawn(db, season["_id"], bot_id)
        forfeited += forfeit_waiting(db, season["_id"], bot_id, now)
    return forfeited


def forfeit_waiting(db: Database, season_id: ObjectId, bot_id: ObjectId, now: datetime) -> int:
    """Ends the bot's waiting games of a season as forfeits; returns how many."""
    query = matches.match_filter(status=matches.QUEUED, bot_id=bot_id, season_id=season_id)
    forfeited = 0
    for match in db[MATCHES].find(query, {"white": 1, "black": 1}):
        # The match goes first: a runner that took the job already finds it ended.
        forfeited += matches.forfeit(db, match, bot_id, now)
        jobs.cancel_match(db, match["_id"], now, running=False)
    return forfeited


def sweep(db: Database, now: datetime) -> int:
    """Forfeits the waiting games of withdrawn bots in running seasons; returns how many."""
    forfeited = 0
    for season in seasons.running(db):
        for bot_id in season["withdrawn"]:
            forfeited += forfeit_waiting(db, season["_id"], bot_id, now)
    return forfeited
