"""GET /bots and /bots/{bot_id}: verified bots only (E15)."""

from flask import Blueprint
from sbm_store import bots

from sbm_api import context
from sbm_api.bot_view import bot_view
from sbm_api.errors import not_found
from sbm_api.params import object_id

blueprint = Blueprint("bots", __name__)


@blueprint.get("/bots")
def list_bots():
    items = [bot for bot in bots.all_by_name(context.db()) if bot["status"] == bots.VERIFIED]
    return {"items": [bot_view(bot) for bot in items]}


@blueprint.get("/bots/<bot_id>")
def get_bot(bot_id: str):
    bot = bots.get(context.db(), object_id(bot_id, "bot_id"))
    if bot is None or bot["status"] != bots.VERIFIED:
        raise not_found("no such bot")
    return bot_view(bot)
