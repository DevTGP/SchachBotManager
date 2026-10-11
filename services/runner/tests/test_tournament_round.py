"""The runner starts a tournament edition, plays it and finishes it (E173–E176)."""

from datetime import timedelta

from sbm_store import (
    disciplines,
    editions,
    matches,
    registrations,
    tournament_setup,
    tournaments,
)
from sbm_store.discipline import Discipline
from sbm_store.names import MATCHES

from sbm_runner.worker import utc_now

# Defined here: several test folders have a conftest, so `from conftest import` may pick another.
QUICK = Discipline("Quick", initial_time_ms=10_000, increment_ms=0, max_moves=3)


def tournament_of(db, reference_bots, **settings) -> dict:
    past = utc_now() - timedelta(hours=1)
    discipline = disciplines.new_discipline(QUICK, created_by=None, now=past)
    assert disciplines.insert(db, discipline)
    tournament = tournaments.new_tournament(
        {
            "name": "Pokal",
            "discipline_id": discipline["_id"],
            "format": tournaments.ROUND_ROBIN,
            "games_per_pairing": 1,
            **settings,
        },
        created_by=None,
        now=past,
    )
    assert tournament_setup.create(db, tournament, past)
    for bot in reference_bots:
        registration = registrations.new_registration(
            tournament["_id"],
            bot["_id"],
            created_by=None,
            now=past,
            target_type=registrations.TOURNAMENT,
        )
        assert registrations.insert(db, registration)
    assert tournament_setup.start(db, tournament["_id"], past)
    return tournament


def test_a_started_edition_is_played_and_finished(db, reference_bots, worker):
    tournament = tournament_of(db, reference_bots)

    assert worker.step()
    first = editions.latest(db, tournament["_id"])
    (game,) = list(db[MATCHES].find({"context.edition_id": first["_id"]}))
    assert game["status"] == matches.FINISHED
    assert game["rated"] is True

    assert not worker.step()

    finished = editions.get(db, first["_id"])
    assert finished["status"] == editions.FINISHED
    assert len(finished["final"]["table"]) == 2
    following = editions.latest(db, tournament["_id"])
    assert (following["number"], following["status"], following["starts_after"]) == (
        2,
        editions.PLANNED,
        None,
    )
