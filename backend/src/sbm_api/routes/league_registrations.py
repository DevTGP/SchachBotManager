"""POST /leagues/{league_id}/registrations and DELETE …/registrations/{bot_id} (E136).

The owner (a coder) or an admin registers a verified bot; it enters at the next season start.
Leaving during a running season withdraws the bot: its waiting games become forfeits.
"""

from flask import Blueprint
from sbm_store import bots, league_withdrawal, leagues, registrations, users

from sbm_api import admin_audit, body, context
from sbm_api.bot_access import visible_bot
from sbm_api.current_user import require_coder
from sbm_api.errors import (
    ALREADY_REGISTERED,
    BOT_STATE,
    LEAGUE_STATE,
    ApiError,
    forbidden,
    not_found,
)
from sbm_api.league_view import registration_view
from sbm_api.params import object_id

blueprint = Blueprint("league_registrations", __name__)


@blueprint.post("/leagues/<league_id>/registrations")
def register_bot(league_id: str):
    user = require_coder()
    db = context.db()
    league = _league(league_id)
    data = body.json_object(("bot_id",))
    bot = _managed_bot(user, body.identifier(data, "bot_id"))
    if league["archived"]:
        raise ApiError(409, LEAGUE_STATE, "the league is archived")
    if bot["status"] != bots.VERIFIED:
        raise ApiError(409, BOT_STATE, "only verified bots may register")
    entry = registrations.new_registration(
        league["_id"], bot["_id"], created_by=user["_id"], now=context.now()
    )
    if not registrations.insert(db, entry):
        raise ApiError(409, ALREADY_REGISTERED, "the bot is registered already", "bot_id")
    _audit(user, bot, "league.register", league)
    # A bot enters at the next start; it has no tier yet.
    return registration_view(entry, league, bot, None), 201


@blueprint.delete("/leagues/<league_id>/registrations/<bot_id>")
def deregister_bot(league_id: str, bot_id: str):
    user = require_coder()
    db = context.db()
    league = _league(league_id)
    bot = _managed_bot(user, object_id(bot_id, "bot_id"))
    if registrations.get_active(db, league["_id"], bot["_id"]) is None:
        raise not_found("the bot is not registered")
    forfeits = league_withdrawal.withdraw(
        db, bot["_id"], registrations.DEREGISTERED, context.now(), league_id=league["_id"]
    )
    _audit(user, bot, "league.deregister", league, {"forfeits": forfeits})
    return "", 204


def _league(league_id: str) -> dict:
    league = leagues.get(context.db(), object_id(league_id, "league_id"))
    if league is None:
        raise not_found("no such league")
    return league


def _managed_bot(user: dict, bot_id) -> dict:
    """The bot if user owns it or is an admin."""
    bot = visible_bot(bots.get(context.db(), bot_id), user)
    if user["role"] != users.ADMIN and bot.get("owner_id") != user["_id"]:
        raise forbidden("only the owner or an admin may do this")
    return bot


def _audit(user: dict, bot: dict, action: str, league: dict, details: dict | None = None) -> None:
    """Only what an admin does to a bot that is not their own goes into the audit log."""
    if user["role"] == users.ADMIN and bot.get("owner_id") != user["_id"]:
        admin_audit.record(user, action, bot["_id"], {"league": league["name"], **(details or {})})
