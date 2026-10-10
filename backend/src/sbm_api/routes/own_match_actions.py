"""POST /matches/{match_id}/withdraw: an account takes a waiting game it set back (E157)."""

from flask import Blueprint
from sbm_store import jobs, matches

from sbm_api import context, rate_limit
from sbm_api.current_user import require_coder
from sbm_api.errors import MATCH_STATE, ApiError, not_found
from sbm_api.params import object_id

blueprint = Blueprint("own_match_actions", __name__)

WITHDRAW_DETAIL = "withdrawn by the requester"


@blueprint.post("/matches/<match_id>/withdraw")
def withdraw_own_match(match_id: str):
    user = require_coder()
    db, now = context.db(), context.now()
    match = matches.get(db, object_id(match_id, "match_id"))
    if match is None or match.get("created_by") != user["_id"]:
        raise not_found("no such match")
    if match["status"] != matches.QUEUED:
        raise _state_error()
    # Only a job no runner holds yet: a game that has begun is played out.
    cancelled = jobs.cancel_match(db, match["_id"], now, running=False)
    if cancelled is None and jobs.running_match(db, match["_id"]):
        raise _state_error()
    if not matches.abort(db, match["_id"], WITHDRAW_DETAIL, now):
        raise _state_error()
    if match.get("counted"):
        rate_limit.give_back_games(user, 1, set_at=match["created_at"])
    return "", 204


def _state_error() -> ApiError:
    return ApiError(409, MATCH_STATE, "only a waiting match can be withdrawn")
