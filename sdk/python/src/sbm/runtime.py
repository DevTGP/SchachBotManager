"""run: the entry point of every bot (spec/api/runtime.json)."""

import os
import sys
import traceback

from sbm import log
from sbm.bot import Bot
from sbm.channel import Channel, ProtocolError, open_stdio, open_tcp
from sbm.game import BotError, Game, guarded
from sbm.log import Log
from sbm.options import Options, OptionsError, parse_options


def _describe(error: BotError) -> str:
    cause = error.__cause__
    if cause is None:
        return str(error)
    return f"{error}\n{''.join(traceback.format_exception(cause)).rstrip()}"


def _open(options: Options) -> Channel:
    if options.transport == "tcp":
        return open_tcp(options.port)
    return open_stdio()


def _play(bot: type[Bot], options: Options) -> None:
    try:
        channel = _open(options)
    except OSError as error:
        Log.error(f"cannot connect to the arena on 127.0.0.1:{options.port}: {error}")
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
