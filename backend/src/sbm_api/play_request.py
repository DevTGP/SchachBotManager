"""The body of POST /play: a game of the person against a verified bot (E114, E115).

Any verified bot may be chosen. The time comes from a discipline in use or is free, at most
30 min + 30 s; the game starts from the standard position.
"""

import secrets
from dataclasses import dataclass

from pymongo.database import Database
from sbm.arena.time_control import format_time_control
from sbm.referee import STANDARD_FEN
from sbm_store.discipline import DEFAULT_MAX_MOVES, Discipline

from sbm_api import body, discipline_request
from sbm_api.enqueue_request import verified_bot

FIELDS = ("bot_id", "color", "discipline_id", "initial_time_ms", "increment_ms")
COLORS = ("white", "black")
MAX_INITIAL_MS = 30 * 60 * 1000
MAX_INCREMENT_MS = 30 * 1000
START_FEN = STANDARD_FEN


@dataclass(frozen=True)
class PlayRequest:
    bot: dict
    color: str
    discipline: Discipline


def parse(db: Database) -> PlayRequest:
    data = body.json_object(FIELDS)
    bot = verified_bot(db, data, "bot_id")
    color = body.choice(data, "color", (*COLORS, "random"))
    if color == "random":
        color = secrets.choice(COLORS)
    discipline = discipline_request.chosen(db, data) or free_times(data)
    return PlayRequest(bot=bot, color=color, discipline=discipline)


def free_times(data: dict) -> Discipline:
    initial_ms = body.integer(data, "initial_time_ms", low=10_000, high=MAX_INITIAL_MS)
    increment_ms = body.integer(data, "increment_ms", low=0, high=MAX_INCREMENT_MS, default=0)
    return Discipline(
        name=format_time_control(initial_ms, increment_ms),
        initial_time_ms=initial_ms,
        increment_ms=increment_ms,
        max_moves=DEFAULT_MAX_MOVES,
    )
