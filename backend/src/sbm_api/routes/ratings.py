"""Public: the rankings of bots (E103) and of players (E118) by rating.

Overall by default, or in the discipline of the query discipline_id (E163).
"""

from flask import Blueprint, request
from sbm_store import rankings

from sbm_api import context
from sbm_api.bot_view import bot_view
from sbm_api.params import optional_object_id
from sbm_api.rating_start import rating_start

blueprint = Blueprint("ratings", __name__)


@blueprint.get("/ratings")
def list_ratings():
    discipline_id = optional_object_id(request.args, "discipline_id")
    ranking = rankings.bot_ranking(context.db(), discipline_id, rating_start())
    return {"items": [{**bot_view(bot), "rating": rating} for bot, rating in ranking]}


@blueprint.get("/ratings/players")
def list_player_ratings():
    discipline_id = optional_object_id(request.args, "discipline_id")
    ranking = rankings.player_ranking(context.db(), discipline_id, rating_start())
    return {"items": [{"username": user["username"], "rating": rating} for user, rating in ranking]}
