"""The runner starts a released season, plays it and finishes it (E132–E135)."""

from datetime import timedelta

from sbm.referee import STANDARD_FEN
from sbm_store import (
    disciplines,
    jobs,
    league_setup,
    leagues,
    matches,
    registrations,
    seasons,
)
from sbm_store.discipline import Discipline
from sbm_store.enqueue import enqueue_match
from sbm_store.names import JOBS, MATCHES

from sbm_runner.worker import utc_now

# Defined here: several test folders have a conftest, so `from conftest import` may pick another.
QUICK = Discipline("Quick", initial_time_ms=10_000, increment_ms=0, max_moves=3)


def league_of(db, reference_bots, **settings) -> dict:
    past = utc_now() - timedelta(hours=1)
    discipline = disciplines.new_discipline(QUICK, created_by=None, now=past)
    assert disciplines.insert(db, discipline)
    league = leagues.new_league(
        {"name": "Liga", "discipline_id": discipline["_id"], "games_per_pairing": 1, **settings},
        created_by=None,
        now=past,
    )
    assert league_setup.create(db, league, past)
    for bot in reference_bots:
        registration = registrations.new_registration(
            league["_id"], bot["_id"], created_by=None, now=past
        )
        assert registrations.insert(db, registration)
    assert league_setup.release(db, league["_id"], past)
    return league


def test_a_released_season_is_played_and_finished(db, reference_bots, worker):
    league = league_of(db, reference_bots)

    assert worker.step()
    first = seasons.latest(db, league["_id"])
    (game,) = list(db[MATCHES].find({"context.season_id": first["_id"]}))
    assert game["status"] == matches.FINISHED
    assert first["status"] == seasons.RUNNING

    assert not worker.step()

    finished = seasons.get(db, first["_id"])
    assert finished["status"] == seasons.FINISHED
    assert len(finished["final"][0]["table"]) == 2
    following = seasons.latest(db, league["_id"])
    assert (following["number"], following["status"]) == (2, seasons.PLANNED)


def test_single_games_and_the_league_take_turns(db, reference_bots, worker):
    random_bot, material = reference_bots
    created = utc_now() - timedelta(hours=2)
    single = [
        enqueue_match(db, random_bot, material, QUICK, start_fen=STANDARD_FEN, now=created)
        for _ in range(2)
    ]
    db[JOBS].update_many({}, {"$set": {"priority": 50}})
    league = league_of(db, reference_bots, games_per_pairing=2)

    worker.step()
    worker.step()

    taken = db[JOBS].find({"type": jobs.MATCH, "status": jobs.DONE}).sort("claimed_at", 1)
    assert [job["competition"] for job in taken] == [
        jobs.SINGLE,
        jobs.league_competition(league["_id"]),
    ]
    assert db[MATCHES].find_one({"_id": single[1]})["status"] == matches.QUEUED
