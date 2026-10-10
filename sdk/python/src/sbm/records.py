"""Records of the bot API (spec/api/types.json): GameInfo, GameResult, Info and PlayedGame."""

from dataclasses import dataclass

from sbm._core import Move


@dataclass(frozen=True)
class GameInfo:
    """Game parameters from init, passed to on_game_start."""

    game_id: str
    color: int
    opponent_name: str
    start_fen: str
    initial_time_ms: int
    increment_ms: int
    startup_ms: int
    memory_limit_mib: int
    discipline: str


@dataclass(frozen=True)
class GameResult:
    """End of the game from game_over, passed to on_game_end."""

    result: str
    termination: str


@dataclass(kw_only=True)
class Info:
    """Search information sent with the move (E43); every field is optional."""

    depth: int | None = None
    seldepth: int | None = None
    score_cp: int | None = None
    score_mate: int | None = None
    nodes: int | None = None
    pv: list[Move] | None = None
    text: str | None = None


@dataclass(frozen=True)
class PlayedGame:
    """One game played with play, from the own bot's point of view."""

    game_id: str
    color: int
    opponent_name: str
    result: str
    termination: str
