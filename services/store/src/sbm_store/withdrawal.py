"""A bot leaving all its leagues and tournaments at once: when it is retired, disabled or
deleted (E136, E179)."""

from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import league_withdrawal, tournament_withdrawal


def withdraw_everywhere(db: Database, bot_id: ObjectId, reason: str, now: datetime) -> int:
    """Returns the games forfeited."""
    return league_withdrawal.withdraw(db, bot_id, reason, now) + tournament_withdrawal.withdraw(
        db, bot_id, reason, now
    )
