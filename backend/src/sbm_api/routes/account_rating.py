"""GET /account/rating: the own rating from rated games against bots (E117)."""

from flask import Blueprint
from sbm_store import ratings

from sbm_api.current_user import require_user
from sbm_api.rating_start import rating_start

blueprint = Blueprint("account_rating", __name__)


@blueprint.get("/account/rating")
def own_rating():
    return ratings.current(require_user(), rating_start())
