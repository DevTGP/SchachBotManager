"""GET /bots/{bot_id}/opponents: the record of a bot against each other bot (E161)."""

from flask import Blueprint
from sbm_store import bots, opponents

from sbm_api import context
from sbm_api.bot_access import visible_bot
from sbm_api.current_user import current_user
from sbm_api.params import object_id

blueprint = Blueprint("bot_opponents", __name__)


@blueprint.get("/bots/<bot_id>/opponents")
def get_bot_opponents(bot_id: str):
    db = context.db()
    bot = visible_bot(bots.get(db, object_id(bot_id, "bot_id")), current_user())
    return {"items": [_opponent(record) for record in opponents.records(db, bot["_id"])]}


def _opponent(record: dict) -> dict:
    return {
        "bot_id": str(record["_id"]),
        "name": record["name"],
        "version": record["version"],
        "games": record["games"],
        "wins": record["wins"],
        "draws": record["draws"],
        "losses": record["losses"],
    }
