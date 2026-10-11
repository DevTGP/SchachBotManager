"""Participants of leagues and tournaments: bots and accounts alike (E182).

An entry, a registration or a match side names a bot by bot_id or an account by user_id; the
other field is None. Its key is the id that is set. Ids are ObjectIds and unique across
collections, so the keys of bots and accounts never collide.
"""

from bson import ObjectId

COLORS = ("white", "black")


def key(item: dict) -> ObjectId:
    """The bot_id of a bot, the user_id of an account."""
    return item.get("bot_id") or item["user_id"]


def is_human(item: dict) -> bool:
    return item.get("bot_id") is None and item.get("user_id") is not None


def side_query(participant: ObjectId) -> dict:
    """Matches in which the participant plays either colour."""
    return {
        "$or": [
            {f"{color}.{field}": participant} for color in COLORS for field in ("bot_id", "user_id")
        ]
    }
