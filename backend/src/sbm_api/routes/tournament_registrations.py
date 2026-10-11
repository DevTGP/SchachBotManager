"""POST /tournaments/{tournament_id}/registrations and DELETE …/registrations/{bot_id} (E179).

Like registering for a league: the owner (a coder) or an admin registers a verified bot and it
enters at the next edition start. Leaving during a running edition withdraws the bot: its
waiting games become forfeits, in knockout it loses its duel.
"""

from flask import Blueprint
from sbm_store import bots, registrations, tournament_withdrawal, tournaments, users

from sbm_api import admin_audit, body, context
from sbm_api.bot_access import visible_bot
from sbm_api.current_user import require_coder
from sbm_api.errors import (
    ALREADY_REGISTERED,
    BOT_STATE,
    TOURNAMENT_STATE,
    ApiError,
    forbidden,
    not_found,
)
from sbm_api.params import object_id
from sbm_api.tournament_view import registration_view

blueprint = Blueprint("tournament_registrations", __name__)
TOURNAMENT = registrations.TOURNAMENT


@blueprint.post("/tournaments/<tournament_id>/registrations")
def register_bot(tournament_id: str):
    user = require_coder()
    db = context.db()
    tournament = _tournament(tournament_id)
    data = body.json_object(("bot_id",))
    bot = _managed_bot(user, body.identifier(data, "bot_id"))
    if tournament["archived"]:
        raise ApiError(409, TOURNAMENT_STATE, "the tournament is archived")
    if bot["status"] != bots.VERIFIED:
        raise ApiError(409, BOT_STATE, "only verified bots may register")
    entry = registrations.new_registration(
        tournament["_id"],
        bot["_id"],
        created_by=user["_id"],
        now=context.now(),
        target_type=TOURNAMENT,
    )
    if not registrations.insert(db, entry):
        raise ApiError(409, ALREADY_REGISTERED, "the bot is registered already", "bot_id")
    _audit(user, bot, "tournament.register", tournament)
    # A bot enters at the next start; it plays in no edition yet.
    return registration_view(entry, tournament, bot, set()), 201


@blueprint.delete("/tournaments/<tournament_id>/registrations/<bot_id>")
def deregister_bot(tournament_id: str, bot_id: str):
    user = require_coder()
    db = context.db()
    tournament = _tournament(tournament_id)
    bot = _managed_bot(user, object_id(bot_id, "bot_id"))
    if registrations.get_active(db, tournament["_id"], bot["_id"], target_type=TOURNAMENT) is None:
        raise not_found("the bot is not registered")
    forfeits = tournament_withdrawal.withdraw(
        db, bot["_id"], registrations.DEREGISTERED, context.now(), tournament_id=tournament["_id"]
    )
    _audit(user, bot, "tournament.deregister", tournament, {"forfeits": forfeits})
    return "", 204


def _tournament(tournament_id: str) -> dict:
    tournament = tournaments.get(context.db(), object_id(tournament_id, "tournament_id"))
    if tournament is None:
        raise not_found("no such tournament")
    return tournament


def _managed_bot(user: dict, bot_id) -> dict:
    """The bot if user owns it or is an admin."""
    bot = visible_bot(bots.get(context.db(), bot_id), user)
    if user["role"] != users.ADMIN and bot.get("owner_id") != user["_id"]:
        raise forbidden("only the owner or an admin may do this")
    return bot


def _audit(
    user: dict, bot: dict, action: str, tournament: dict, details: dict | None = None
) -> None:
    """Only what an admin does to a bot that is not their own goes into the audit log."""
    if user["role"] == users.ADMIN and bot.get("owner_id") != user["_id"]:
        details = {"tournament": tournament["name"], **(details or {})}
        admin_audit.record(user, action, bot["_id"], details)
