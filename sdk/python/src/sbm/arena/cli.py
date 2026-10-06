"""sbm-arena: plays games between two bots on the developer's machine (lokale-entwicklung.md).

Exit codes: 0 done, 1 the arena itself failed, 2 invalid arguments, 130 interrupted.
"""

import argparse
import contextlib
import datetime
import sys
from collections.abc import Sequence

from sbm.arena.bot_spec import parse_bot, unique_names
from sbm.arena.entrants import create_entrant
from sbm.arena.pgn import GameInfo, to_pgn
from sbm.arena.replay import replay_fen
from sbm.arena.report import ConsoleReport
from sbm.arena.series import Game, Series
from sbm.arena.time_control import parse_time_control
from sbm.referee import STANDARD_FEN, MatchRecord, MatchSettings

EVENT = "sbm-arena"
SITE = "local"
EXIT_FAILED = 1
EXIT_INTERRUPTED = 130


def _positive(text: str) -> int:
    if not text.isdigit() or int(text) < 1:
        raise argparse.ArgumentTypeError(f"{text!r} is not a positive whole number")
    return int(text)


def _non_negative(text: str) -> int:
    if not text.isdigit():
        raise argparse.ArgumentTypeError(f"{text!r} is not a whole number")
    return int(text)


def _parser() -> argparse.ArgumentParser:
    defaults = MatchSettings(initial_time_ms=1)
    parser = argparse.ArgumentParser(
        prog="sbm-arena",
        description="Plays games between two chess bots by the SchachBotManager protocol.",
        epilog=(
            "A bot is a .py file (run with this Python), a command line such as "
            '"java -jar bot.jar", tcp[:PORT] for a bot started in an IDE with --tcp, '
            "or a reference bot: random, material."
        ),
    )
    parser.add_argument("white", help="the bot with white in the first game")
    parser.add_argument("black", help="the bot with black in the first game")
    parser.add_argument(
        "--games", type=_positive, default=1, help="number of games, colors alternate"
    )
    parser.add_argument(
        "--time", default="60+1", help="seconds per game plus increment per move (default 60+1)"
    )
    parser.add_argument(
        "--no-clock", action="store_true", help="no time limits, e.g. for breakpoints"
    )
    parser.add_argument("--fen", help="start position (default: the standard position)")
    parser.add_argument(
        "--replay", metavar="PGN", help="start where a recorded game stands, see --replay-ply"
    )
    parser.add_argument(
        "--replay-game", type=_positive, metavar="N", help="game in the PGN file (default 1)"
    )
    parser.add_argument(
        "--replay-ply",
        type=_non_negative,
        metavar="N",
        help="half-moves to replay before the bots take over (default: all)",
    )
    parser.add_argument("--pgn", metavar="PATH", help="append the games to this PGN file")
    parser.add_argument("--moves", action="store_true", help="print each move")
    parser.add_argument("--quiet", action="store_true", help="hide the bots' log output")
    parser.add_argument(
        "--startup-ms", type=_positive, default=defaults.startup_ms, help="time to send ready"
    )
    parser.add_argument(
        "--tolerance-ms",
        type=int,
        default=defaults.tolerance_ms,
        help="grace time per move for transport delays",
    )
    parser.add_argument(
        "--max-moves",
        type=_positive,
        default=defaults.max_moves,
        help="full moves until the game is drawn",
    )
    return parser


def _settings(args: argparse.Namespace) -> MatchSettings:
    initial_ms, increment_ms = parse_time_control(args.time)
    return MatchSettings(
        initial_time_ms=initial_ms,
        increment_ms=increment_ms,
        startup_ms=args.startup_ms,
        tolerance_ms=args.tolerance_ms,
        max_moves=args.max_moves,
        start_fen=_start_fen(args),
        clock=not args.no_clock,
    )


def _start_fen(args: argparse.Namespace) -> str:
    if args.replay is None:
        if args.replay_game is not None or args.replay_ply is not None:
            raise ValueError("--replay-game and --replay-ply need --replay")
        return args.fen or STANDARD_FEN
    if args.fen is not None:
        raise ValueError("--fen and --replay cannot be used together")
    try:
        with open(args.replay, encoding="utf-8-sig", errors="replace") as file:
            pgn = file.read()
        return replay_fen(pgn, args.replay_game or 1, args.replay_ply)
    except (OSError, ValueError) as error:
        raise ValueError(f"--replay: {error}") from None


def _status(text: str) -> None:
    print(text, file=sys.stderr, flush=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        specs = unique_names([parse_bot(args.white), parse_bot(args.black)])
        settings = _settings(args)
    except ValueError as error:
        parser.error(str(error))
    if args.replay is not None:
        _status(f"start position from {args.replay}: {settings.start_fen}")

    entrants = []
    with contextlib.ExitStack() as stack:
        try:
            for spec in specs:
                entrant = create_entrant(spec, None if args.quiet else sys.stderr, _status)
                stack.callback(entrant.close)
                entrants.append(entrant)
            pgn = stack.enter_context(open(args.pgn, "a", encoding="utf-8")) if args.pgn else None
        except OSError as error:
            _status(f"error: {error}")
            return EXIT_FAILED

        report = ConsoleReport(sys.stdout, settings.start_fen, args.games)
        dates: dict[int, str] = {}

        def start(game: Game) -> None:
            dates[game.number] = datetime.date.today().strftime("%Y.%m.%d")
            report.start(game)

        def end(game: Game, record: MatchRecord) -> None:
            report.end(game, record)
            if pgn is not None:
                info = GameInfo(EVENT, SITE, dates[game.number], game.number)
                pgn.write(to_pgn(record, settings, info) + "\n")
                pgn.flush()

        series = Series(entrants[0], entrants[1], settings, args.games)
        try:
            series.play(on_start=start, on_move=report.move if args.moves else None, on_end=end)
        except KeyboardInterrupt:
            _status("interrupted")
            return EXIT_INTERRUPTED
        except OSError as error:
            _status(f"error: {error}")
            return EXIT_FAILED
        report.scores(series.scores)
    return 0
