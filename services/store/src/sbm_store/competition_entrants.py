"""Who of the registered may start in a season or edition (E136, E179, E182).

A bot must be verified, an account active. holders gives their documents, which also hold the
ratings (E163, E117); eligible the entry fields: bot_id or user_id, name and version (None for
an account).
"""

from bson import ObjectId
from pymongo.database import Database

from sbm_store import bots, participants, users


def holders(db: Database, registrations: list[dict]) -> dict[ObjectId, dict]:
    """The verified bots and active accounts among the registrations, by participant key."""
    bot_ids = [entry["bot_id"] for entry in registrations if entry.get("bot_id") is not None]
    user_ids = [entry["user_id"] for entry in registrations if participants.is_human(entry)]
    return bots.by_ids(db, bot_ids, status=bots.VERIFIED) | users.by_ids(db, user_ids, active=True)


def eligible(db: Database, registrations: list[dict]) -> dict[ObjectId, dict]:
    return {key: fields(holder) for key, holder in holders(db, registrations).items()}


def fields(holder: dict) -> dict:
    """The entry fields of a bot or an account document."""
    if "username" in holder:
        return {
            "bot_id": None,
            "user_id": holder["_id"],
            "name": holder["username"],
            "version": None,
        }
    return {
        "bot_id": holder["_id"],
        "user_id": None,
        "name": holder["name"],
        "version": holder.get("version"),
    }
