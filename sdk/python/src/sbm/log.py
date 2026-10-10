"""Log: the debug log of the bot (spec/api/log.json), written to stderr.

Each line carries time, ply and level: ``14:03:27.512 [ply 12] INFO  message``. The SDK sets the
start level and an optional file from the command line or environment (E61) and the ply from
each turn.
"""

import sys
from collections.abc import Callable
from datetime import datetime
from typing import TextIO

from sbm.constants import DEBUG, ERROR, INFO, OFF, TRACE, WARN
from sbm.errors import InvalidArgumentError

LEVEL_NAMES = ("TRACE", "DEBUG", "INFO", "WARN", "ERROR", "OFF")


class _State:
    level = INFO
    ply: int | None = None
    file: TextIO | None = None
    # Receives level, time and text of every written line: the viewer window (E106).
    listener: Callable[[int, str, str], None] | None = None


def _check_level(function: str, level: int) -> int:
    if not isinstance(level, int):
        raise TypeError(f"Log.{function}: level must be an int, not {type(level).__name__}")
    if not TRACE <= level <= OFF:
        raise InvalidArgumentError(f"Log.{function}: unknown level {level}")
    return level


def _write(level: int, message: object) -> None:
    if level < _State.level:
        return
    time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    ply = "-" if _State.ply is None else _State.ply
    line = f"{time} [ply {ply}] {LEVEL_NAMES[level]:<5} {message}\n"
    sys.stderr.write(line)
    sys.stderr.flush()
    if _State.file is not None:
        _State.file.write(line)
        _State.file.flush()
    if _State.listener is not None:
        _State.listener(level, time, str(message))


class Log:
    """Debug log with the levels TRACE < DEBUG < INFO < WARN < ERROR < OFF; static only."""

    def __init__(self) -> None:
        raise TypeError("Log has only static functions")

    @staticmethod
    def trace(message: str) -> None:
        """Writes at level TRACE."""
        _write(TRACE, message)

    @staticmethod
    def debug(message: str) -> None:
        """Writes at level DEBUG."""
        _write(DEBUG, message)

    @staticmethod
    def info(message: str) -> None:
        """Writes at level INFO."""
        _write(INFO, message)

    @staticmethod
    def warn(message: str) -> None:
        """Writes at level WARN."""
        _write(WARN, message)

    @staticmethod
    def error(message: str) -> None:
        """Writes at level ERROR."""
        _write(ERROR, message)

    @staticmethod
    def set_level(level: int) -> None:
        """Sets the minimum level written; OFF writes nothing."""
        _State.level = _check_level("set_level", level)

    @staticmethod
    def level() -> int:
        """Current minimum level; INFO unless the command line or environment says otherwise."""
        return _State.level

    @staticmethod
    def is_enabled(level: int) -> bool:
        """Whether a message at that level would be written."""
        return _State.level <= _check_level("is_enabled", level) < OFF


def configure(level: int, file: TextIO | None) -> None:
    """Start level and optional log file, set by run before the game."""
    _State.level = level
    _State.file = file


def set_listener(listener: Callable[[int, str, str], None] | None) -> None:
    """Also hands every written line to the listener; None ends that."""
    _State.listener = listener


def set_ply(ply: int | None) -> None:
    """Ply shown in each line from the current turn on."""
    _State.ply = ply
