"""run: the entry point of every bot (spec/api/runtime.json)."""

import os
import sys
import traceback

from sbm import log
from sbm.arena.time_control import parse_time_control
from sbm.bot import Bot
from sbm.channel import Channel, ProtocolError, open_stdio, open_tcp
from sbm.game import BotError, Game, guarded
from sbm.log import Log
from sbm.options import Options, OptionsError, RemoteOptions, parse_options


def _describe(error: BotError) -> str:
    cause = error.__cause__
    if cause is None:
        return str(error)
    return f"{error}\n{''.join(traceback.format_exception(cause)).rstrip()}"


class RemoteError(Exception):
    """Raised by _open_remote; the remote modules load only for a remote game."""


def _open(options: Options) -> Channel:
    if options.transport == "remote":
        return _open_remote(options.remote)
    if options.transport == "tcp":
        return open_tcp(options.port)
    return open_stdio()


def _open_remote(remote: RemoteOptions) -> Channel:
    """Asks the server for the game and takes its seat (E116).

    The modules for HTTP, TLS and WebSocket load only here, so a bot in the sandbox never
    imports them.
    """
    from sbm.remote import game_request
    from sbm.remote.channel import RemoteChannel

    body = {"opponent": remote.opponent, "color": remote.color}
    if remote.discipline:
        body["discipline"] = remote.discipline
    else:
        try:
            initial_ms, increment_ms = parse_time_control(remote.time)
        except ValueError as error:
            raise RemoteError(str(error)) from None
        body |= {"initial_time_ms": initial_ms, "increment_ms": increment_ms}
    try:
        seat = game_request.request_game(remote.url, remote.token, body)
        Log.info(f"remote game {seat.match_id} against {remote.opponent}, playing {seat.color}")
        return RemoteChannel.join(seat)
    except game_request.RemoteError as error:
        raise RemoteError(str(error)) from None


def _play(bot: type[Bot], options: Options) -> None:
    try:
        channel = _open(options)
    except RemoteError as error:
        Log.error(str(error))
        sys.exit(1)
    except OSError as error:
        where = options.remote.url if options.remote else f"the arena on 127.0.0.1:{options.port}"
        Log.error(f"cannot connect to {where}: {error}")
        sys.exit(1)
    with channel:
        try:
            Game(guarded(f"{bot.__name__}()", bot), channel).play()
        except BotError as error:
            Log.error(_describe(error))
            sys.exit(1)
        except ProtocolError as error:
            Log.error(f"protocol error: {error}")
            sys.exit(1)


def run(bot: type[Bot]) -> None:
    """Creates one instance of the bot class and plays one game with it.

    Transport and log level come from the command line or environment (E61): --tcp [PORT],
    --log-level LEVEL, --log-file PATH or SBM_TRANSPORT, SBM_PORT, SBM_LOG_LEVEL, SBM_LOG_FILE.
    --remote URL with SBM_TOKEN and --opponent NAME plays against a bot on the server (E116).
    An exception from the bot is logged at ERROR and ends the process with exit code 1 (E49).
    """
    if not (isinstance(bot, type) and issubclass(bot, Bot)):
        raise TypeError(f"run: bot must be a subclass of sbm.Bot, not {bot!r}")
    try:
        options = parse_options(sys.argv[1:], os.environ)
    except OptionsError as error:
        sys.exit(f"sbm: {error}")
    file = None
    if options.log_file is not None:
        try:
            file = open(options.log_file, "a", encoding="utf-8")  # noqa: SIM115
        except OSError as error:
            sys.exit(f"sbm: cannot open the log file: {error}")
    log.configure(options.log_level, file)
    try:
        _play(bot, options)
    finally:
        log.configure(Log.level(), None)
        if file is not None:
            file.close()
