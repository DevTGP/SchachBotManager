"""GET /series/{series_id}: the games of one request and the score (E155)."""

from flask import Blueprint
from sbm_store import matches

from sbm_api import context
from sbm_api.errors import not_found
from sbm_api.params import object_id
from sbm_api.series_view import series_view

blueprint = Blueprint("series", __name__)


@blueprint.get("/series/<series_id>")
def get_series(series_id: str):
    games = matches.of_series(context.db(), object_id(series_id, "series_id"))
    if not games:
        raise not_found("no such series")
    return series_view(series_id, games)
