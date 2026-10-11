"""GET /bots/{bot_id}/seasons, /rating-history and /record: the history of a bot version
(E139-E141)."""

from flask import Blueprint
from pymongo.database import Database
from sbm_store import bot_record, bot_seasons, bots, disciplines, rating_history

from sbm_api import context
from sbm_api.bot_access import visible_bot
from sbm_api.bot_record_view import bot_record_view
from sbm_api.bot_season_view import bot_season_view
from sbm_api.current_user import current_user
from sbm_api.params import object_id
from sbm_api.rating_history_view import rating_history_view

blueprint = Blueprint("bot_history", __name__)


@blueprint.get("/bots/<bot_id>/seasons")
def get_bot_seasons(bot_id: str):
    db = context.db()
    bot = _bot(db, bot_id)
    return {"items": [bot_season_view(found) for found in bot_seasons.of_bot(db, bot["_id"])]}


@blueprint.get("/bots/<bot_id>/rating-history")
def get_bot_rating_history(bot_id: str):
    db = context.db()
    bot = _bot(db, bot_id)
    return rating_history_view(rating_history.of_bot(db, bot["_id"]), _discipline_names(db))


@blueprint.get("/bots/<bot_id>/record")
def get_bot_record(bot_id: str):
    db = context.db()
    bot = _bot(db, bot_id)
    return bot_record_view(bot_record.by_discipline(db, bot["_id"]), _discipline_names(db))


def _bot(db: Database, bot_id: str) -> dict:
    return visible_bot(bots.get(db, object_id(bot_id, "bot_id")), current_user())


def _discipline_names(db: Database) -> dict:
    """There are few disciplines; all of them are read at once."""
    return {discipline["_id"]: discipline["name"] for discipline in disciplines.all_by_name(db)}
