"""Participants of leagues and tournaments as the API shows them: a bot or an account that plays
in person (schema LeagueBot, E182)."""

from bson import ObjectId
from pymongo.database import Database
from sbm_store import bots, competition_entrants, participants, users


def participant(entry: dict) -> dict:
    """An entry, table row, registration holder or match side with bot_id or user_id."""
    bot_id = entry.get("bot_id")
    user_id = entry.get("user_id")
    return {
        "kind": "bot" if bot_id is not None else "human",
        "bot_id": None if bot_id is None else str(bot_id),
        "user_id": None if bot_id is not None or user_id is None else str(user_id),
        "name": entry["name"],
        "version": entry.get("version"),
    }


def holders(db: Database, registrations: list[dict]) -> dict[ObjectId, dict]:
    """The current entry fields of the registered bots and accounts, by participant key."""
    bot_ids = [entry["bot_id"] for entry in registrations if entry.get("bot_id") is not None]
    user_ids = [entry["user_id"] for entry in registrations if participants.is_human(entry)]
    found = bots.by_ids(db, bot_ids) | users.by_ids(db, user_ids)
    return {key: competition_entrants.fields(holder) for key, holder in found.items()}
