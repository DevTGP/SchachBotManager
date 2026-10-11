"""GET /leagues, /leagues/{league_id}, /seasons/{season_id} and /bots/{bot_id}/leagues (E137)."""

from flask import Blueprint
from sbm_store import bots, competition_entrants, leagues, seasons

from sbm_api import context
from sbm_api.bot_access import visible_bot
from sbm_api.current_user import current_user
from sbm_api.errors import not_found
from sbm_api.league_view import bot_registrations, league_detail, league_list
from sbm_api.params import object_id
from sbm_api.season_view import season_view

blueprint = Blueprint("leagues", __name__)


@blueprint.get("/leagues")
def list_leagues():
    return {"items": league_list(context.db())}


@blueprint.get("/leagues/<league_id>")
def get_league(league_id: str):
    db = context.db()
    league = leagues.get(db, object_id(league_id, "league_id"))
    if league is None:
        raise not_found("no such league")
    return league_detail(db, league)


@blueprint.get("/seasons/<season_id>")
def get_season(season_id: str):
    db = context.db()
    season = seasons.get(db, object_id(season_id, "season_id"))
    if season is None:
        raise not_found("no such season")
    return season_view(db, season)


@blueprint.get("/bots/<bot_id>/leagues")
def get_bot_leagues(bot_id: str):
    db = context.db()
    bot = visible_bot(bots.get(db, object_id(bot_id, "bot_id")), current_user())
    return {"items": bot_registrations(db, competition_entrants.fields(bot))}
