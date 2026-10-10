"""Public: the rankings of bots (E103) and of players (E118) by rating."""

from flask import Blueprint
from sbm_store import ratings

from sbm_api import context
from sbm_api.bot_view import bot_view
from sbm_api.rating_start import rating_start

blueprint = Blueprint("ratings", __name__)


@blueprint.get("/ratings")
def list_ratings():
    return {"items": [bot_view(bot) for bot in ratings.ranking(context.db())]}


@blueprint.get("/ratings/players")
def list_player_ratings():
    return {
        "items": [
            {"username": user["username"], "rating": ratings.current(user, rating_start())}
            for user in ratings.player_ranking(context.db())
        ]
    }
