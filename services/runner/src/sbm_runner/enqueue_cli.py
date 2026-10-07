"""Entry point sbm-enqueue: queues games between bots by name (E71: a dev tool until M3)."""

import argparse
import os
import sys
from datetime import datetime

from bson import ObjectId
from pymongo.database import Database
from sbm.arena.time_control import format_time_control, parse_time_control
from sbm.referee import STANDARD_FEN, MatchSettings
from sbm_store import bots
from sbm_store.connection import database_from_env
from sbm_store.discipline import DEFAULT_MAX_MOVES, DEFAULT_STARTUP_MS, Discipline
from sbm_store.enqueue import DEFAULT_PRIORITY, enqueue_match

from sbm_runner.worker import utc_now


class EnqueueError(ValueError):
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sbm-enqueue",
        description="Queue games between two bots; the database comes from SBM_MONGO_URI.",
    )
    parser.add_argument("white", help="name of the bot with white, e.g. Random")
    parser.add_argument("black", help="name of the bot with black, e.g. Material")
    parser.add_argument("--time", default="60+1", help="seconds+increment (default: 60+1)")
    parser.add_argument("--games", type=int, default=1, help="number of games (default: 1)")
    parser.add_argument("--alternate", action="store_true", help="swap colors after every game")
    parser.add_argument("--priority", type=int, default=DEFAULT_PRIORITY)
    parser.add_argument("--fen", help="start position (default: the standard position)")
    parser.add_argument("--max-moves", type=int, default=DEFAULT_MAX_MOVES)
    parser.add_argument("--startup-ms", type=int, default=DEFAULT_STARTUP_MS)
    parser.add_argument("--discipline", help="name of the discipline (default: the time)")
    return parser


def discipline_from_args(args: argparse.Namespace) -> Discipline:
    initial_ms, increment_ms = parse_time_control(args.time)
    discipline = Discipline(
        name=args.discipline or format_time_control(initial_ms, increment_ms),
        initial_time_ms=initial_ms,
        increment_ms=increment_ms,
        startup_ms=args.startup_ms,
        max_moves=args.max_moves,
    )
    # The referee's checks apply here already, so no queued match fails to start later.
    MatchSettings(
        initial_time_ms=discipline.initial_time_ms,
        increment_ms=discipline.increment_ms,
        startup_ms=discipline.startup_ms,
        tolerance_ms=discipline.tolerance_ms,
        max_moves=discipline.max_moves,
        start_fen=args.fen or STANDARD_FEN,
        discipline=discipline.name,
    )
    return discipline


def enqueue_games(db: Database, args: argparse.Namespace, now: datetime) -> list[ObjectId]:
    if args.games < 1:
        raise EnqueueError("--games must be at least 1")
    discipline = discipline_from_args(args)
    white, black = (_bot(db, name) for name in (args.white, args.black))
    ids = []
    for _ in range(args.games):
        ids.append(
            enqueue_match(
                db,
                white,
                black,
                discipline,
                start_fen=args.fen or STANDARD_FEN,
                now=now,
                priority=args.priority,
            )
        )
        if args.alternate:
            white, black = black, white
    return ids


def _bot(db: Database, name: str) -> dict:
    bot = bots.by_name(db, name)
    if bot is None:
        known = ", ".join(bot["name"] for bot in bots.all_by_name(db)) or "none"
        raise EnqueueError(f"no bot named {name!r}; known bots: {known}")
    return bot


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        ids = enqueue_games(database_from_env(os.environ), args, utc_now())
    except (ValueError, RuntimeError) as error:
        print(f"sbm-enqueue: {error}", file=sys.stderr)
        return 2
    for match_id in ids:
        print(match_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
