"""Shared values of the negative suite; conftest.py holds the fixtures."""

from pathlib import Path

from bson import ObjectId
from sbm.referee import MatchSettings
from sbm_store.bots import BUILTIN_PREFIX

BOTS = Path(__file__).parent / "bots"
RANDOM = {"_id": ObjectId(), "name": "Random", "source_ref": f"{BUILTIN_PREFIX}random_mover"}
QUICK = MatchSettings(initial_time_ms=10_000, increment_ms=0, max_moves=3)
# Endings of a game in which both bots played by the rules.
REGULAR = {
    "max_moves",
    "checkmate",
    "stalemate",
    "insufficient_material",
    "threefold_repetition",
    "fifty_move_rule",
}
