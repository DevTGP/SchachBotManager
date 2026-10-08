"""GET /account/bots: the own bots in every status, newest first (E91)."""

from flask import Blueprint
from sbm_store import bots

from sbm_api import context
from sbm_api.bot_view import bot_view
from sbm_api.current_user import require_user

blueprint = Blueprint("account_bots", __name__)


@blueprint.get("/account/bots")
def list_own_bots():
    user = require_user()
    return {"items": [bot_view(bot) for bot in bots.of_owner(context.db(), user["_id"])]}
