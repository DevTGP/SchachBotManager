"""The body of POST /matches: games an account sets for its own bots (E98).

Tighter than the admin's request: from the standard position, a limited number of games, and
behind the admin's matches in the queue. Any discipline in use may be chosen (E100); free times
have the default move limit. The limits are settings of coders (E154).
"""

from pymongo.database import Database
from sbm.arena.time_control import format_time_control
from sbm.referee import STANDARD_FEN
from sbm_store import coder_settings
from sbm_store.coder_settings import CoderSettings
from sbm_store.discipline import DEFAULT_MAX_MOVES, Discipline

from sbm_api import body, discipline_request
from sbm_api.enqueue_request import EnqueueRequest, verified_bot
from sbm_api.errors import invalid_parameter

FIELDS = (
    "white_bot_id",
    "black_bot_id",
    "discipline_id",
    "initial_time_ms",
    "increment_ms",
    "games",
    "alternate",
)


def parse(db: Database, user: dict) -> EnqueueRequest:
    data = body.json_object(FIELDS)
    limits = coder_settings.get(db)
    white = verified_bot(db, data, "white_bot_id")
    black = verified_bot(db, data, "black_bot_id")
    if user["_id"] not in (white.get("owner_id"), black.get("owner_id")):
        raise invalid_parameter("white_bot_id", "one of the bots must be your own")
    discipline = discipline_request.chosen(db, data) or free_times(data, limits)
    return EnqueueRequest(
        white=white,
        black=black,
        discipline=discipline,
        start_fen=STANDARD_FEN,
        games=body.integer(data, "games", low=1, high=limits.games_per_request, default=1),
        alternate=body.boolean(data, "alternate", default=False),
        priority=limits.priority,
    )


def free_times(data: dict, limits: CoderSettings) -> Discipline:
    initial_ms = body.integer(data, "initial_time_ms", low=1000, high=limits.max_initial_ms)
    increment_ms = body.integer(
        data, "increment_ms", low=0, high=limits.max_increment_ms, default=0
    )
    return Discipline(
        name=format_time_control(initial_ms, increment_ms),
        initial_time_ms=initial_ms,
        increment_ms=increment_ms,
        max_moves=DEFAULT_MAX_MOVES,
    )
