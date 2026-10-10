"""GET /account/rating: the own overall rating from rated games against bots (E117, E163)."""

from flask import Blueprint
from sbm_store import rating_values

from sbm_api.current_user import require_user
from sbm_api.rating_start import rating_start

blueprint = Blueprint("account_rating", __name__)


@blueprint.get("/account/rating")
def own_rating():
    return rating_values.overall(require_user(), rating_start())
