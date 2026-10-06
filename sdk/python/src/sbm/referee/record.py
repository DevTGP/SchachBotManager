"""What the referee records about a game (match-runner.md, datenmodell.md)."""

from dataclasses import dataclass, field

from sbm.referee.outcome import Outcome


@dataclass(frozen=True)
class MoveRecord:
    """One move: ply counts from 0 at the start position, fen is the position after the move.

    remaining_ms is the mover's time after the move including the increment.
    """

    ply: int
    uci: str
    san: str
    fen: str
    elapsed_ms: int
    remaining_ms: int
    info: dict | None


@dataclass(frozen=True)
class SideRecord:
    """A side as it introduced itself in ready; sdk and lang stay None if it never did."""

    name: str
    sdk: str | None = None
    lang: str | None = None


@dataclass
class MatchRecord:
    start_fen: str
    white: SideRecord
    black: SideRecord
    moves: list[MoveRecord] = field(default_factory=list)
    outcome: Outcome | None = None
