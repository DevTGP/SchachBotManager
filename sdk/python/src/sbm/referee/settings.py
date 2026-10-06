"""Settings of one game: time control, start position and limits (match-runner.md)."""

import re
from dataclasses import dataclass

from sbm._core import Board
from sbm.errors import ChessError

STANDARD_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
MAX_MILLISECONDS = 2**53 - 1
MAX_NAME_LENGTH = 64
GAME_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")


@dataclass(frozen=True, kw_only=True)
class MatchSettings:
    """Everything the referee needs besides the two players; checked on creation.

    With clock=False no deadline applies, neither for startup nor for turns, and the remaining
    times stay at initial_time_ms (debugging with breakpoints). max_moves counts full moves;
    when it is reached without another ending, the game is drawn.
    """

    initial_time_ms: int
    increment_ms: int = 0
    startup_ms: int = 10_000
    tolerance_ms: int = 20
    max_moves: int = 500
    start_fen: str = STANDARD_FEN
    game_id: str = "local"
    discipline: str = "Local"
    memory_limit_mib: int = 1024
    clock: bool = True

    def __post_init__(self) -> None:
        _check_range("initial_time_ms", self.initial_time_ms, 1, MAX_MILLISECONDS)
        _check_range("increment_ms", self.increment_ms, 0, MAX_MILLISECONDS)
        _check_range("startup_ms", self.startup_ms, 1, MAX_MILLISECONDS)
        _check_range("tolerance_ms", self.tolerance_ms, 0, MAX_MILLISECONDS)
        _check_range("max_moves", self.max_moves, 1, MAX_MILLISECONDS)
        _check_range("memory_limit_mib", self.memory_limit_mib, 1, MAX_MILLISECONDS)
        if not isinstance(self.game_id, str) or not GAME_ID.fullmatch(self.game_id):
            raise ValueError(f"game_id {self.game_id!r} must be 1 to 64 of A-Z a-z 0-9 _ -")
        check_name("discipline", self.discipline)
        if not isinstance(self.clock, bool):
            raise TypeError(f"clock must be a bool, not {type(self.clock).__name__}")
        try:
            Board.from_fen(self.start_fen)
        except (ChessError, TypeError) as error:
            raise ValueError(f"start_fen: {error}") from None


def check_name(field: str, name: object) -> None:
    """Display names in init have 1 to 64 characters (common.schema.json)."""
    if not isinstance(name, str) or not 1 <= len(name) <= MAX_NAME_LENGTH:
        raise ValueError(f"{field} {name!r} must be a str of 1 to {MAX_NAME_LENGTH} characters")


def _check_range(field: str, value: object, low: int, high: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{field} must be an int, not {type(value).__name__}")
    if not low <= value <= high:
        raise ValueError(f"{field}={value} is outside {low}..{high}")
