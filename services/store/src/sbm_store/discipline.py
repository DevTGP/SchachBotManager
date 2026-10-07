"""The conditions of a match, copied into it as discipline_snapshot (ligen-turniere.md)."""

from dataclasses import asdict, dataclass

DEFAULT_STARTUP_MS = 10_000
DEFAULT_TOLERANCE_MS = 20
DEFAULT_MAX_MOVES = 500


@dataclass(frozen=True)
class Discipline:
    name: str
    initial_time_ms: int
    increment_ms: int = 0
    startup_ms: int = DEFAULT_STARTUP_MS
    tolerance_ms: int = DEFAULT_TOLERANCE_MS
    max_moves: int = DEFAULT_MAX_MOVES

    def to_document(self) -> dict:
        return asdict(self)

    @classmethod
    def from_document(cls, document: dict) -> "Discipline":
        return cls(**document)
