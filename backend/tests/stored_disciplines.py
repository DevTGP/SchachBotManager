"""Disciplines stored directly in the database for the tests (E100)."""

from sbm_store import disciplines
from sbm_store.discipline import Discipline

from stored_games import NOW


def store_discipline(db, name: str, *, archived: bool = False, **settings) -> dict:
    settings = {"initial_time_ms": 60_000} | settings
    discipline = disciplines.new_discipline(
        Discipline(name=name, **settings), created_by=None, now=NOW
    )
    discipline["archived"] = archived
    assert disciplines.insert(db, discipline)
    return discipline
