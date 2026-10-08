"""The body of POST /admin/matches: which games to queue, checked as the referee would (E85).

enqueue puts the games of a parsed request into the queue, also for POST /matches (E98).
"""

from dataclasses import dataclass
from datetime import datetime

from bson import ObjectId
from pymongo.database import Database
from sbm.arena.time_control import format_time_control
from sbm.referee import STANDARD_FEN, MatchSettings
from sbm_store import bots
from sbm_store.discipline import DEFAULT_MAX_MOVES, Discipline
from sbm_store.enqueue import DEFAULT_PRIORITY, enqueue_match

from sbm_api import body, discipline_request
from sbm_api.errors import invalid_parameter

FIELDS = (
    "white_bot_id",
    "black_bot_id",
    "discipline_id",
    "initial_time_ms",
    "increment_ms",
    "games",
    "alternate",
    "priority",
    "max_moves",
    "start_fen",
)


@dataclass(frozen=True)
class EnqueueRequest:
    white: dict
    black: dict
    discipline: Discipline
    start_fen: str
    games: int
    alternate: bool
    priority: int


def parse(db: Database) -> EnqueueRequest:
    data = body.json_object(FIELDS)
    white = verified_bot(db, data, "white_bot_id")
    black = verified_bot(db, data, "black_bot_id")
    discipline = discipline_request.chosen(db, data) or free_times(data)
    start_fen = body.string(data, "start_fen", max_length=100, default=None) or STANDARD_FEN
    _check_settings(discipline, start_fen)
    return EnqueueRequest(
        white=white,
        black=black,
        discipline=discipline,
        start_fen=start_fen,
        games=body.integer(data, "games", low=1, high=100, default=1),
        alternate=body.boolean(data, "alternate", default=False),
        priority=body.integer(data, "priority", low=0, high=1000, default=DEFAULT_PRIORITY),
    )


def free_times(data: dict) -> Discipline:
    """Named after the time control, e.g. 180+2."""
    initial_ms = body.integer(data, "initial_time_ms", low=1000, high=86_400_000)
    increment_ms = body.integer(data, "increment_ms", low=0, high=3_600_000, default=0)
    return Discipline(
        name=format_time_control(initial_ms, increment_ms),
        initial_time_ms=initial_ms,
        increment_ms=increment_ms,
        max_moves=body.integer(data, "max_moves", low=1, high=2000, default=DEFAULT_MAX_MOVES),
    )


def enqueue(db: Database, order: EnqueueRequest, *, now: datetime) -> list[ObjectId]:
    """Queues the games in order; the colours swap after each game if asked."""
    white, black = order.white, order.black
    ids = []
    for _ in range(order.games):
        ids.append(
            enqueue_match(
                db,
                white,
                black,
                order.discipline,
                start_fen=order.start_fen,
                now=now,
                priority=order.priority,
            )
        )
        if order.alternate:
            white, black = black, white
    return ids


def verified_bot(db: Database, data: dict, field: str) -> dict:
    bot = bots.get(db, body.identifier(data, field))
    if bot is None or bot["status"] != bots.VERIFIED:
        raise invalid_parameter(field, f"{field} is not a verified bot")
    return bot


def _check_settings(discipline: Discipline, start_fen: str) -> None:
    """The referee's checks, so no queued match fails to start later."""
    try:
        MatchSettings(
            initial_time_ms=discipline.initial_time_ms,
            increment_ms=discipline.increment_ms,
            startup_ms=discipline.startup_ms,
            tolerance_ms=discipline.tolerance_ms,
            max_moves=discipline.max_moves,
            start_fen=start_fen,
            discipline=discipline.name,
        )
    except ValueError as error:
        # The time fields are in range already, so only the position can be wrong.
        raise invalid_parameter("start_fen", str(error)) from error
