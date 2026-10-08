"""POST /play: a person against a verified bot, as guest or with an account (E11, E114)."""

from flask import Blueprint
from sbm_store import matches, play

from sbm_api import context, play_limits, play_request
from sbm_api.current_user import current_user
from sbm_api.play_view import seat_view

blueprint = Blueprint("play", __name__)

GUEST_NAME = "Guest"


@blueprint.post("/play")
def start_game():
    db, now = context.db(), context.now()
    order = play_request.parse(db)
    user = current_user()
    user_id = None if user is None else user["_id"]
    requested_by = play.origin(ip_key=play_limits.ip_key(), user_id=user_id, token_id=None)
    play_limits.check_and_count(requested_by)
    seat, seat_hash = play.new_seat()
    name = GUEST_NAME if user is None else user["username"]
    person = play.seat_side(play.HUMAN, name, user_id=user_id, seat_hash=seat_hash)
    bot = matches.side(order.bot)
    white, black = (person, bot) if order.color == "white" else (bot, person)
    match_id = play.create(
        db,
        play.HUMAN,
        white,
        black,
        order.discipline,
        start_fen=play_request.START_FEN,
        now=now,
        requested_by=requested_by,
    )
    return seat_view(match_id, seat, order.color), 201
