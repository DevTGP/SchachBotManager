"""GET /seasons/{season_id}/schedule: the rounds of one tier with their games (E138)."""

from flask import Blueprint, request
from sbm_store import season_schedule, seasons

from sbm_api import context
from sbm_api.errors import invalid_parameter, not_found
from sbm_api.params import integer, object_id
from sbm_api.schedule_view import schedule_view

blueprint = Blueprint("season_schedule", __name__)
MAX_TIER = 10


@blueprint.get("/seasons/<season_id>/schedule")
def get_season_schedule(season_id: str):
    db = context.db()
    if "tier" not in request.args:
        raise invalid_parameter("tier", "tier is required")
    tier = integer(request.args, "tier", default=1, low=1, high=MAX_TIER)
    season = seasons.get(db, object_id(season_id, "season_id"))
    if season is None:
        raise not_found("no such season")
    rounds = season_schedule.rounds(db, season, tier)
    if rounds is None:
        raise not_found("no such tier")
    return schedule_view(tier, rounds)
