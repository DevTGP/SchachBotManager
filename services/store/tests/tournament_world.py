"""Tournaments, registrations and results for the store tests of tournaments and editions."""

import random

from bson import ObjectId
from conftest import BLITZ, T0

from sbm_store import (
    disciplines,
    edition_progress,
    edition_start,
    editions,
    matches,
    registrations,
    tournament_setup,
    tournaments,
)
from sbm_store.migrate import migrate
from sbm_store.names import MATCHES


def add_tournament(db, format: str, name: str = "Pokal", **settings) -> dict:
    """A migrated database with a new tournament and its first edition, waiting for an admin."""
    migrate(db)
    discipline = disciplines.new_discipline(BLITZ, created_by=None, now=T0)
    if not disciplines.insert(db, discipline):
        discipline = db["disciplines"].find_one({"name_key": "blitz"})
    tournament = tournaments.new_tournament(
        {"name": name, "discipline_id": discipline["_id"], "format": format, **settings},
        created_by=None,
        now=T0,
    )
    assert tournament_setup.create(db, tournament, T0)
    return tournament


def enter(db, tournament: dict, entrants: list[dict]) -> None:
    for bot in entrants:
        registration = registrations.new_registration(
            tournament["_id"],
            bot["_id"],
            created_by=bot["owner_id"],
            now=T0,
            target_type=registrations.TOURNAMENT,
        )
        assert registrations.insert(db, registration)


def start(db, tournament: dict, now=T0, seed: int = 1) -> dict:
    """Starts the waiting edition now and returns it running."""
    tournament_setup.start(db, tournament["_id"], now)
    (started,) = edition_start.start_due(db, now, random.Random(seed))
    return editions.get(db, started)


def edition_matches(db, edition_id: ObjectId, status: str | None = None) -> list[dict]:
    query = matches.match_filter(status=status, edition_id=edition_id)
    return list(db[MATCHES].find(query).sort("_id", 1))


def finish_waiting(db, edition_id: ObjectId, result_of) -> int:
    """Ends each waiting game of the edition with result_of(match); returns how many."""
    waiting = edition_matches(db, edition_id, matches.QUEUED)
    for match in waiting:
        db[MATCHES].update_one(
            {"_id": match["_id"]},
            {
                "$set": {
                    "status": matches.FINISHED,
                    "result": result_of(match),
                    "termination": "checkmate",
                }
            },
        )
        db["jobs"].update_one({"payload.match_id": match["_id"]}, {"$set": {"status": "done"}})
    return len(waiting)


def stronger(order: list[dict]):
    """A result_of where the bot earlier in order always wins."""
    rank = {bot["_id"]: number for number, bot in enumerate(order)}

    def result_of(match: dict) -> str:
        white, black = match["white"]["bot_id"], match["black"]["bot_id"]
        return "1-0" if rank[white] < rank[black] else "0-1"

    return result_of


def draws(match: dict) -> str:
    return "1/2-1/2"


def play_to_the_end(db, edition_id: ObjectId, result_of, now=T0, limit: int = 50) -> dict:
    """Ticks the edition and ends its games until it is finished; returns it."""
    rng = random.Random(3)
    for _ in range(limit):
        edition_progress.advance_running(db, now, rng)
        edition = editions.get(db, edition_id)
        if edition["status"] == editions.FINISHED:
            return edition
        finish_waiting(db, edition_id, result_of)
    raise AssertionError("the edition did not finish")
