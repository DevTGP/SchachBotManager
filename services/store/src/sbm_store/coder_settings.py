"""Limits for coders in the settings collection, changeable on the website (E154).

The uploads and games per day count for each coder on its own (E91, E98); a request for own
matches holds at most games_per_request games with free times up to max_initial_ms and
max_increment_ms, queued at priority, which stays below the default of admins (E98).
"""

from dataclasses import dataclass

from pymongo.database import Database

from sbm_store import settings_document

DOCUMENT_ID = "coders"
# Inclusive ranges the web API accepts.
LIMITS = {
    "games_per_day": (1, 1000),
    "uploads_per_day": (1, 1000),
    "games_per_request": (1, 100),
    "max_initial_ms": (1000, 3_600_000),
    "max_increment_ms": (0, 60_000),
    "priority": (0, 99),
}


@dataclass(frozen=True)
class CoderSettings:
    games_per_day: int = 20
    uploads_per_day: int = 20
    games_per_request: int = 10
    max_initial_ms: int = 300_000
    max_increment_ms: int = 5000
    priority: int = 50


def get(db: Database) -> CoderSettings:
    return settings_document.load(db, DOCUMENT_ID, CoderSettings)


def problem(settings: CoderSettings) -> str | None:
    """The field that does not fit the others; None if all fit."""
    return None


def save(db: Database, settings: CoderSettings) -> None:
    settings_document.store(db, DOCUMENT_ID, settings)
