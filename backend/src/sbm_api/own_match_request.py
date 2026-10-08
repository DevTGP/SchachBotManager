"""The body of POST /matches: games an account sets for its own bots (E98).

Tighter than the admin's request: from the standard position with the default move limit, at
most 5 min + 5 s and 10 games, and behind the admin's matches in the queue.
"""

from pymongo.database import Database
from sbm.arena.time_control import format_time_control
from sbm.referee import STANDARD_FEN
from sbm_store.discipline import DEFAULT_MAX_MOVES, Discipline

from sbm_api import body
from sbm_api.enqueue_request import EnqueueRequest, verified_bot
from sbm_api.errors import invalid_parameter

FIELDS = (
    "white_bot_id",
    "black_bot_id",
    "initial_time_ms",
    "increment_ms",
    "games",
    "alternate",
)
MAX_INITIAL_MS = 5 * 60 * 1000
MAX_INCREMENT_MS = 5000
MAX_GAMES = 10
# Admins queue with 100 by default (DEFAULT_PRIORITY).
PRIORITY = 50


def parse(db: Database, user: dict) -> EnqueueRequest:
    data = body.json_object(FIELDS)
    white = verified_bot(db, data, "white_bot_id")
    black = verified_bot(db, data, "black_bot_id")
    if user["_id"] not in (white.get("owner_id"), black.get("owner_id")):
        raise invalid_parameter("white_bot_id", "one of the bots must be your own")
    initial_ms = body.integer(data, "initial_time_ms", low=1000, high=MAX_INITIAL_MS)
    increment_ms = body.integer(data, "increment_ms", low=0, high=MAX_INCREMENT_MS, default=0)
    discipline = Discipline(
        name=format_time_control(initial_ms, increment_ms),
        initial_time_ms=initial_ms,
        increment_ms=increment_ms,
        max_moves=DEFAULT_MAX_MOVES,
    )
    return EnqueueRequest(
        white=white,
        black=black,
        discipline=discipline,
        start_fen=STANDARD_FEN,
        games=body.integer(data, "games", low=1, high=MAX_GAMES, default=1),
        alternate=body.boolean(data, "alternate", default=False),
        priority=PRIORITY,
    )
