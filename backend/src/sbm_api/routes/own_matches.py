"""POST /matches: single games set by coders for their own bots (E98)."""

from flask import Blueprint

from sbm_api import context, enqueue_request, own_match_request, rate_limit
from sbm_api.current_user import require_user

blueprint = Blueprint("own_matches", __name__)


@blueprint.post("/matches")
def enqueue_own_matches():
    user = require_user()
    db = context.db()
    order = own_match_request.parse(db, user)
    # Counted once the request is valid, so a mistake costs no games.
    rate_limit.count_games(user, order.games)
    ids = enqueue_request.enqueue(db, order, now=context.now())
    return {"match_ids": [str(match_id) for match_id in ids]}, 201
