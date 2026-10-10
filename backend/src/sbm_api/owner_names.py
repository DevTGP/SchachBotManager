"""The username of a bot's creator, public since E164; read once per owner and request."""

from bson import ObjectId
from flask import g
from sbm_store import users

from sbm_api import context


def owner_name(owner_id: ObjectId | None) -> str | None:
    """None for reference bots, which have no owner (E72)."""
    if owner_id is None:
        return None
    names = g.setdefault("owner_names", {})
    if owner_id not in names:
        owner = users.get(context.db(), owner_id)
        names[owner_id] = owner["username"] if owner else None
    return names[owner_id]
