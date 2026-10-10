"""POST /matches: single games set by coders for their own bots (E98)."""

from flask import Blueprint

from sbm_api import context, enqueue_request, own_match_request, rate_limit
from sbm_api.current_user import require_coder

blueprint = Blueprint("own_matches", __name__)


@blueprint.post("/matches")
def enqueue_own_matches():
    user = require_coder()
    db = context.db()
    order = own_match_request.parse(db, user)
    # Counted once the request is valid, so a mistake costs no games.
    rate_limit.count_games(user, order.games)
    enqueued = enqueue_request.enqueue(
        db, order, now=context.now(), created_by=user["_id"], counted=True
    )
    return enqueued.response(), 201
