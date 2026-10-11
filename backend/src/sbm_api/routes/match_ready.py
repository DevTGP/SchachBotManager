"""POST /matches/{match_id}/ready: the account of a side of a released league or tournament
game says it is ready and present (E183); the page repeats it while it waits."""

import re

from flask import Blueprint, request
from sbm_store import competition_readiness, matches, play, tokens

from sbm_api import body, context
from sbm_api.current_user import require_user
from sbm_api.errors import MATCH_STATE, ApiError, forbidden, invalid_parameter, not_found
from sbm_api.params import object_id
from sbm_api.play_view import seat_view

blueprint = Blueprint("match_ready", __name__)

SEAT = re.compile(r"[A-Za-z0-9_-]{43}")
NOT_WAITING = "the match does not wait for readiness"


@blueprint.post("/matches/<match_id>/ready")
def ready(match_id: str):
    user = require_user()
    sent = _sent_seat()
    db, now = context.db(), context.now()
    match_oid = object_id(match_id, "match_id")
    match = matches.get(db, match_oid)
    if match is None:
        raise not_found("no such match")
    color = competition_readiness.color_of(match, user["_id"])
    if color is None or not competition_readiness.is_competition(match):
        raise forbidden("the account plays no side of this match")
    if not competition_readiness.waiting_for_ready(match):
        raise ApiError(409, MATCH_STATE, NOT_WAITING)
    # The page keeps its seat while it fits, so a second tab does not take the seat away.
    if sent is not None and tokens.token_hash(sent) == match[color].get("seat_hash"):
        seat, seat_hash = sent, match[color]["seat_hash"]
    else:
        seat, seat_hash = play.new_seat()
    if competition_readiness.mark_ready(db, match_oid, color, seat_hash, now) is None:
        raise ApiError(409, MATCH_STATE, NOT_WAITING)
    return seat_view(match_oid, seat, color)


def _sent_seat() -> str | None:
    """The seat of the optional body; no body is an empty one."""
    if not request.get_data():
        return None
    data = body.json_object(("seat",))
    seat = data.get("seat")
    if seat is None:
        return None
    if not isinstance(seat, str) or SEAT.fullmatch(seat) is None:
        raise invalid_parameter("seat", "seat must be a seat token of 43 characters")
    return seat
