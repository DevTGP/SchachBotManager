"""GET /account/rating: the own rating from rated games against bots, overall and per discipline
(E117, E163, E169)."""

from flask import Blueprint
from sbm_store import disciplines, rating_values

from sbm_api import context
from sbm_api.current_user import require_user
from sbm_api.rating_start import rating_start

blueprint = Blueprint("account_rating", __name__)


@blueprint.get("/account/rating")
def own_rating():
    user = require_user()
    start = rating_start()
    played = []
    for discipline in disciplines.all_by_name(context.db()):
        rating = rating_values.in_discipline(user, discipline["_id"], start)
        if rating["games"] > 0:
            played.append(
                {"discipline_id": str(discipline["_id"]), "name": discipline["name"], **rating}
            )
    return {**rating_values.overall(user, start), "disciplines": played}
