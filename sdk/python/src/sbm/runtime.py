"""run: the entry point of every bot (spec/api/runtime.json)."""

import os
import sys

from sbm import log
from sbm.bot import Bot
from sbm.channel import Channel, ProtocolError, open_stdio, open_tcp
from sbm.game import BotError, Game, describe, guarded
from sbm.log import Log
from sbm.options import Options, OptionsError, RemoteOptions, parse_options
from sbm.viewer import open_window


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
    from sbm.remote.opening import open_game

    try:
        _, channel = open_game(remote)
    except game_request.RemoteError as error:
        raise RemoteError(str(error)) from None
    return channel


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
            Log.error(describe(error))
            sys.exit(1)
        except ProtocolError as error:
            Log.error(f"protocol error: {error}")
            sys.exit(1)


def run(bot: type[Bot], viewer: bool = False) -> None:
    """Creates one instance of the bot class and plays one game with it.

    Transport and log level come from the command line or environment (E61): --tcp [PORT],
    --log-level LEVEL, --log-file PATH or SBM_TRANSPORT, SBM_PORT, SBM_LOG_LEVEL, SBM_LOG_FILE.
    --remote URL with SBM_TOKEN and --opponent NAME plays against a bot on the server (E116).
    viewer=True shows the game in the viewer window; the program then ends once it is closed (E108).
    An exception from the bot is logged at ERROR and ends the process with exit code 1 (E49).
    """
    if not (isinstance(bot, type) and issubclass(bot, Bot)):
        raise TypeError(f"run: bot must be a subclass of sbm.Bot, not {bot!r}")
    if not isinstance(viewer, bool):
        raise TypeError(f"run: viewer must be True or False, not {viewer!r}")
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
    if viewer:
        open_window()
    try:
        _play(bot, options)
    finally:
        log.configure(Log.level(), None)
        if file is not None:
            file.close()
