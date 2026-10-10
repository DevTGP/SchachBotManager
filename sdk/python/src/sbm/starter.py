"""play: games from code, locally or against a bot on the server (spec/api/runtime.json, E120).

The arena and the remote modules load only when play runs, so a bot in the sandbox never
imports them. All arguments are checked before the first game starts.
"""

import os
import random
import sys
from collections.abc import Callable
from urllib.parse import urlsplit

from sbm.bot import Bot
from sbm.channel import ProtocolError
from sbm.constants import BLACK, WHITE
from sbm.errors import InvalidArgumentError
from sbm.game import BotError, describe
from sbm.log import Log, set_ply
from sbm.options import COLORS, DEFAULT_TIME
from sbm.records import PlayedGame
from sbm.viewer import open_window

TOKEN_VARIABLE = "SBM_TOKEN"
COLOR_NAMES = ("white", "black")

# Plays game number (from 1) with the own bot in the given color.
Round = Callable[[int, int], PlayedGame]


def _check(
    bot: object, opponent: object, color: object, time: object, games: object
) -> tuple[str, int]:
    """Common checks; returns the color name and the number of games."""
    if not (isinstance(bot, type) and issubclass(bot, Bot)):
        raise TypeError(f"play: bot must be a subclass of sbm.Bot, not {bot!r}")
    if not isinstance(opponent, str) or not opponent.strip():
        raise InvalidArgumentError("play: opponent must be a non-empty str")
    if not isinstance(color, str) or color.lower() not in COLORS:
        raise InvalidArgumentError(f"play: color must be one of {', '.join(COLORS)}")
    if time is not None and not isinstance(time, str):
        raise TypeError(f"play: time must be a str like '60+1', not {type(time).__name__}")
    if not isinstance(games, int) or isinstance(games, bool) or games < 1:
        raise InvalidArgumentError(f"play: games must be an int of at least 1, not {games!r}")
    return color.lower(), games


def _time_control(time: str | None) -> tuple[int, int]:
    from sbm.arena.time_control import parse_time_control

    try:
        return parse_time_control(time or DEFAULT_TIME)
    except ValueError as error:
        raise InvalidArgumentError(f"play: {error}") from None


def _local(bot: type[Bot], opponent: str, time: str | None, discipline: str | None) -> Round:
    from sbm.arena.bot_spec import BotSpec, BotSpecError, parse_bot, unique_names
    from sbm.arena.local_game import play_local
    from sbm.referee import MatchSettings
    from sbm.referee.settings import MAX_NAME_LENGTH

    if discipline:
        raise InvalidArgumentError("play: a discipline needs a server; locally use time")
    initial_ms, increment_ms = _time_control(time)
    try:
        other = parse_bot(opponent)
    except BotSpecError as error:
        raise InvalidArgumentError(f"play: opponent: {error}") from None
    if other.command is None:
        raise InvalidArgumentError("play: a TCP opponent is not possible; use sbm-arena")
    own, other = unique_names([BotSpec(bot.__name__[:MAX_NAME_LENGTH]), other])
    settings = MatchSettings(initial_time_ms=initial_ms, increment_ms=increment_ms)
    return lambda color, number: play_local(bot, own.name, other, color, settings, number)


def _remote(
    bot: type[Bot],
    opponent: str,
    server: str,
    token: str | None,
    time: str | None,
    discipline: str | None,
) -> Round:
    from sbm.options import RemoteOptions
    from sbm.remote.remote_game import play_remote

    parts = urlsplit(server)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise InvalidArgumentError(f"play: server must be an http or https address: {server!r}")
    token = token or os.environ.get(TOKEN_VARIABLE)
    if not token:
        raise InvalidArgumentError(f"play: a server needs a token, or {TOKEN_VARIABLE} set")
    if discipline and time:
        raise InvalidArgumentError("play: give either a discipline or a time, not both")
    if not discipline:
        _time_control(time)

    def one(color: int, number: int) -> PlayedGame:
        remote = RemoteOptions(
            url=server,
            token=token,
            opponent=opponent,
            color=COLOR_NAMES[color],
            discipline=discipline or None,
            time=time or DEFAULT_TIME,
        )
        return play_remote(bot, remote)

    return one


def _failures(server: str | None) -> tuple[type[Exception], ...]:
    """Errors that end play with a message instead of a traceback, besides the bot's own."""
    if not server:
        return (OSError,)
    from sbm.remote.game_request import RemoteError

    return (RemoteError, OSError)


def _report(game: PlayedGame, number: int, games: int) -> None:
    set_ply(None)
    Log.info(
        f"game {number}/{games} ({game.game_id}) as {COLOR_NAMES[game.color]} "
        f"against {game.opponent_name}: {game.result} {game.termination}"
    )


def _points(game: PlayedGame) -> float | None:
    if game.result == "1/2-1/2":
        return 0.5
    if game.result in ("1-0", "0-1"):
        return 1.0 if ("1-0", "0-1").index(game.result) == game.color else 0.0
    return None


def _report_score(played: list[PlayedGame]) -> None:
    points = [_points(game) for game in played]
    scored = [value for value in points if value is not None]
    Log.info(
        f"score {sum(scored):g}/{len(scored)}: {scored.count(1.0)} won, {scored.count(0.5)} drawn, "
        f"{scored.count(0.0)} lost, {points.count(None)} without result"
    )


def play(
    bot: type[Bot],
    opponent: str,
    server: str | None = None,
    token: str | None = None,
    color: str = "random",
    time: str | None = None,
    discipline: str | None = None,
    games: int = 1,
    viewer: bool = False,
) -> list[PlayedGame]:
    """Plays games of the bot class against opponent and returns them in order (E120).

    Without server locally, the opponent being random, material, a bot file or a command; with
    server against the bot of that name on the site, with token or SBM_TOKEN.
    color is the own color in the first game (white, black or random); colors then alternate.
    time is SECONDS+INCREMENT (default 60+1), discipline a discipline on the server instead.
    viewer=True shows all games in one viewer window; after the last one the program waits until
    it is closed (E108).
    Wrong arguments raise InvalidArgumentError or TypeError; an exception of the bot, a refused
    game or a lost connection is logged at ERROR and ends the process with exit code 1.
    """
    color, games = _check(bot, opponent, color, time, games)
    if not isinstance(viewer, bool):
        raise TypeError(f"play: viewer must be True or False, not {viewer!r}")
    if server:
        round_ = _remote(bot, opponent, server, token, time, discipline)
    else:
        round_ = _local(bot, opponent, time, discipline)
    failures = _failures(server)
    first = random.choice((WHITE, BLACK)) if color == "random" else COLOR_NAMES.index(color)
    if viewer:
        open_window()
    played: list[PlayedGame] = []
    try:
        for number in range(1, games + 1):
            own_color = first if number % 2 else 1 - first
            played.append(round_(own_color, number))
            _report(played[-1], number, games)
    except BotError as error:
        Log.error(describe(error))
        sys.exit(1)
    except ProtocolError as error:
        Log.error(f"protocol error: {error}")
        sys.exit(1)
    except failures as error:
        Log.error(f"play stopped: {error}")
        sys.exit(1)
    _report_score(played)
    return played
