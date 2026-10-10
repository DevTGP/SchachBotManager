"""How the queue estimates when a waiting match starts (E154).

A discipline's duration is the mean of its last recent_games finished matches; without any,
the web API assumes moves_per_game moves on each side.
"""

from dataclasses import dataclass

from pymongo.database import Database

from sbm_store import settings_document

DOCUMENT_ID = "estimate"
# Inclusive ranges the web API accepts.
LIMITS = {"recent_games": (1, 200), "moves_per_game": (1, 1000)}


@dataclass(frozen=True)
class EstimateSettings:
    recent_games: int = 20
    moves_per_game: int = 80


def get(db: Database) -> EstimateSettings:
    return settings_document.load(db, DOCUMENT_ID, EstimateSettings)


def problem(settings: EstimateSettings) -> str | None:
    """The field that does not fit the others; None if all fit."""
    return None


def save(db: Database, settings: EstimateSettings) -> None:
    settings_document.store(db, DOCUMENT_ID, settings)
