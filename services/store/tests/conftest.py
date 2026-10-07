from datetime import UTC, datetime

import pytest

from sbm_store import bots
from sbm_store.discipline import Discipline
from sbm_store.migrate import migrate

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
BLITZ = Discipline("Blitz", initial_time_ms=60_000, increment_ms=1000)
T0 = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)


@pytest.fixture
def reference_bots(db) -> tuple[dict, dict]:
    migrate(db)
    return bots.by_name(db, "Random"), bots.by_name(db, "Material")
