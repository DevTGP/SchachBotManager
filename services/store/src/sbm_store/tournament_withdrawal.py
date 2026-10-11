"""A bot or an account leaving its tournaments (E179, E182), like leaving a league
(league_withdrawal).

Leaving ends the active registrations. In a running edition the participant counts as
withdrawn: its waiting games end unplayed as forfeit wins of the opponents, a game already
running is played to the end and counts; in knockout it loses its duel. The runner sweeps the
withdrawn participants of running editions each round, so a crash in between leaves no waiting
game behind.
"""

from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import editions, jobs, matches, registrations
from sbm_store.names import MATCHES


def withdraw(
    db: Database,
    participant: ObjectId,
    reason: str,
    now: datetime,
    *,
    tournament_id: ObjectId | None = None,
) -> int:
    """Takes the bot or account out of all its tournaments, or only tournament_id; returns the games
    forfeited."""
    registrations.leave(
        db, participant, reason, now, target_type=registrations.TOURNAMENT, target_id=tournament_id
    )
    forfeited = 0
    for edition in editions.running_with_bot(db, participant, tournament_id):
        editions.add_withdrawn(db, edition["_id"], participant)
        forfeited += forfeit_waiting(db, edition["_id"], participant, now)
    return forfeited


def forfeit_waiting(
    db: Database, edition_id: ObjectId, participant: ObjectId, now: datetime
) -> int:
    """Ends the participant's waiting games of an edition as forfeits; returns how many."""
    query = matches.match_filter(
        status=matches.QUEUED, participant=participant, edition_id=edition_id
    )
    forfeited = 0
    for match in db[MATCHES].find(query, {"white": 1, "black": 1}):
        # The match goes first: a runner that took the job already finds it ended.
        forfeited += matches.forfeit(db, match, participant, now, detail=matches.LEFT_TOURNAMENT)
        jobs.cancel_match(db, match["_id"], now, running=False)
    return forfeited


def sweep(db: Database, edition: dict, now: datetime) -> int:
    """Forfeits the waiting games of the edition's withdrawn participants; returns how many."""
    return sum(
        forfeit_waiting(db, edition["_id"], participant, now)
        for participant in edition["withdrawn"]
    )
