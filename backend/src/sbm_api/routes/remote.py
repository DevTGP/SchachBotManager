"""POST /remote/matches: a coder's local bot against a verified bot, with an API token (E116).

The local bot then joins its seat over the gateway and speaks the bot protocol v1; its moves
count like those of any bot; the game is never rated but public (E103, E115, E119).
"""

from flask import Blueprint
from sbm_store import matches, play

from sbm_api import context, play_limits, play_request, remote_request
from sbm_api.play_view import seat_view
from sbm_api.token_auth import require_token_user

blueprint = Blueprint("remote", __name__)


@blueprint.post("/remote/matches")
def start_remote_match():
    user, token = require_token_user()
    db, now = context.db(), context.now()
    order = remote_request.parse(db)
    requested_by = play.origin(
        ip_key=play_limits.ip_key(), user_id=user["_id"], token_id=token["_id"]
    )
    play_limits.check_and_count(requested_by)
    seat, seat_hash = play.new_seat()
    local = play.seat_side(play.REMOTE, user["username"], user_id=user["_id"], seat_hash=seat_hash)
    bot = matches.side(order.bot)
    white, black = (local, bot) if order.color == "white" else (bot, local)
    match_id = play.create(
        db,
        play.REMOTE,
        white,
        black,
        order.discipline,
        start_fen=play_request.START_FEN,
        now=now,
        requested_by=requested_by,
    )
    return seat_view(match_id, seat, order.color), 201
