"""The conditions of a match, copied into it as discipline_snapshot (ligen-turniere.md).

A match queued under a stored discipline keeps its discipline_id (E100); one with free times has
None there.
"""

from dataclasses import asdict, dataclass

from bson import ObjectId

DEFAULT_STARTUP_MS = 10_000
DEFAULT_TOLERANCE_MS = 20
DEFAULT_MAX_MOVES = 500
# The same position as sbm.referee.STANDARD_FEN; the store does not depend on the sdk.
STANDARD_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


@dataclass(frozen=True)
class Discipline:
    name: str
    initial_time_ms: int
    increment_ms: int = 0
    startup_ms: int = DEFAULT_STARTUP_MS
    tolerance_ms: int = DEFAULT_TOLERANCE_MS
    max_moves: int = DEFAULT_MAX_MOVES
    discipline_id: ObjectId | None = None

    def to_document(self) -> dict:
        return asdict(self)

    @classmethod
    def from_document(cls, document: dict) -> "Discipline":
        return cls(**document)


def is_rated(discipline: Discipline, start_fen: str) -> bool:
    """Only games under a stored discipline from the standard position count (E100)."""
    return discipline.discipline_id is not None and start_fen == STANDARD_FEN
