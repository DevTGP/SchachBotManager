"""Tournaments and their editions written through the store for the tests (E172–E179)."""

import random
from datetime import timedelta

from sbm_store import (
    edition_progress,
    edition_start,
    editions,
    matches,
    registrations,
    tournament_setup,
    tournaments,
)
from sbm_store.names import MATCHES

from stored_disciplines import store_discipline
from stored_games import NOW


def store_tournament(
    db,
    name: str = "Pokal",
    format: str = tournaments.ROUND_ROBIN,
    discipline: dict | None = None,
    **settings,
) -> dict:
    if discipline is None:
        discipline = store_discipline(db, f"{name} Blitz")
    fields = {"name": name, "discipline_id": discipline["_id"], "format": format} | settings
    tournament = tournaments.new_tournament(fields, created_by=None, now=NOW)
    assert tournament_setup.create(db, tournament, NOW)
    return tournament


def enter(db, tournament: dict, entrants: list[dict]) -> None:
    for bot in entrants:
        entry = registrations.new_registration(
            tournament["_id"],
            bot["_id"],
            created_by=None,
            now=NOW,
            target_type=registrations.TOURNAMENT,
        )
        assert registrations.insert(db, entry)


def start_edition(db, tournament: dict, entrants: list[dict]) -> dict:
    """Registers the bots, starts the waiting edition and its first round; returns it."""
    enter(db, tournament, entrants)
    assert tournament_setup.start(db, tournament["_id"], NOW)
    later = NOW + timedelta(seconds=1)
    (started,) = edition_start.start_due(db, later, random.Random(1))
    tick(db)
    return editions.get(db, started)


def tick(db) -> None:
    """Moves the running editions on as the runner does."""
    edition_progress.advance_running(db, NOW + timedelta(seconds=1), random.Random(1))


def finish_waiting(db, edition: dict, result: str = "1-0") -> int:
    """Ends each waiting game of the edition with result; returns how many."""
    query = matches.match_filter(status=matches.QUEUED, edition_id=edition["_id"])
    waiting = [match["_id"] for match in db[MATCHES].find(query, {"_id": 1})]
    db[MATCHES].update_many(
        {"_id": {"$in": waiting}},
        {"$set": {"status": matches.FINISHED, "result": result, "termination": "checkmate"}},
    )
    db["jobs"].delete_many({"payload.match_id": {"$in": waiting}})
    return len(waiting)
