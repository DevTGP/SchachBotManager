"""Who may register or deregister a participant of a league or tournament (E136, E179, E182).

A bot: its owner or an admin, and it must be verified to register. An account: the account
itself in any role, or an admin, and it must be active to register.
"""

from bson import ObjectId
from sbm_store import bots, users

from sbm_api import admin_audit, body, context
from sbm_api.bot_access import visible_bot
from sbm_api.errors import (
    BOT_STATE,
    USER_STATE,
    ApiError,
    forbidden,
    invalid_parameter,
    not_found,
)

FIELDS = ("bot_id", "user_id")


def registrant(user: dict) -> dict:
    """The bot or account the request body names, checked; a document of either."""
    data = body.json_object(FIELDS)
    named = [field for field in FIELDS if field in data]
    if len(named) != 1:
        raise invalid_parameter("body", "give either bot_id or user_id")
    if named[0] == "bot_id":
        bot = _managed_bot(user, body.identifier(data, "bot_id"))
        if bot["status"] != bots.VERIFIED:
            raise ApiError(409, BOT_STATE, "only verified bots may register")
        return bot
    account = _managed_account(user, body.identifier(data, "user_id"))
    if not account["active"]:
        raise ApiError(409, USER_STATE, "only active accounts may register")
    return account


def managed(user: dict, participant_id: ObjectId) -> dict:
    """The bot or account with this id if user may deregister it."""
    db = context.db()
    bot = bots.get(db, participant_id)
    if bot is not None:
        return _managed_bot(user, participant_id)
    if users.get(db, participant_id) is None:
        raise not_found("no such bot or account")
    return _managed_account(user, participant_id)


def is_account(holder: dict) -> bool:
    return "username" in holder


def audit(user: dict, holder: dict, action: str, details: dict) -> None:
    """Only what an admin does to a bot or account that is not their own goes into the audit
    log; actions on accounts carry the suffix _account."""
    if user["role"] != users.ADMIN:
        return
    if is_account(holder):
        if holder["_id"] != user["_id"]:
            admin_audit.record(user, f"{action}_account", holder["_id"], details)
    elif holder.get("owner_id") != user["_id"]:
        admin_audit.record(user, action, holder["_id"], details)


def _managed_bot(user: dict, bot_id: ObjectId) -> dict:
    """The bot if user owns it or is an admin."""
    bot = visible_bot(bots.get(context.db(), bot_id), user)
    if user["role"] != users.ADMIN and bot.get("owner_id") != user["_id"]:
        raise forbidden("only the owner or an admin may do this")
    return bot


def _managed_account(user: dict, user_id: ObjectId) -> dict:
    """The account if it is user's own or user is an admin."""
    if user_id == user["_id"]:
        return user
    if user["role"] != users.ADMIN:
        raise forbidden("only the account itself or an admin may do this")
    account = users.get(context.db(), user_id)
    if account is None:
        raise not_found("no such account")
    return account
