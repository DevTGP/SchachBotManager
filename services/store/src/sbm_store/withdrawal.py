"""A bot or account leaving all its leagues and tournaments at once: when the bot is retired,
disabled or deleted, or the account deactivated (E136, E179, E182)."""

from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import league_withdrawal, tournament_withdrawal


def withdraw_everywhere(db: Database, participant: ObjectId, reason: str, now: datetime) -> int:
    """Returns the games forfeited."""
    return league_withdrawal.withdraw(
        db, participant, reason, now
    ) + tournament_withdrawal.withdraw(db, participant, reason, now)
