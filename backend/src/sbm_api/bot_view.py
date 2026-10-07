"""Bots as the API shows them (schema Bot); source and owner stay hidden (E15)."""

from sbm_store import bots

from sbm_api.timestamps import timestamp


def bot_view(bot: dict) -> dict:
    return {
        "id": str(bot["_id"]),
        "name": bot["name"],
        "language": bot["language"],
        "status": bot["status"],
        "builtin": bots.is_builtin(bot),
        "created_at": timestamp(bot["created_at"]),
    }
