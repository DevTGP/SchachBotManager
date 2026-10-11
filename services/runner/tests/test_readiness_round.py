"""Each runner round releases, starts and ends the league games of accounts (E183, E184)."""

from datetime import timedelta

from sbm_store import (
    competition_readiness,
    disciplines,
    jobs,
    league_setup,
    leagues,
    matches,
    play,
    registrations,
    users,
)
from sbm_store.discipline import Discipline
from sbm_store.names import JOBS, MATCHES

from sbm_runner.worker import Worker, utc_now

QUICK = Discipline("Quick", initial_time_ms=10_000, increment_ms=0, max_moves=3)


def league_with_account(db, bot: dict) -> dict:
    """A running league of the bot and the account alice, one game between them."""
    past = utc_now() - timedelta(hours=1)
    discipline = disciplines.new_discipline(QUICK, created_by=None, now=past)
    assert disciplines.insert(db, discipline)
    league = leagues.new_league(
        {"name": "Liga", "discipline_id": discipline["_id"], "games_per_pairing": 1},
        created_by=None,
        now=past,
    )
    assert league_setup.create(db, league, past)
    alice = users.new_user("alice", "", users.PLAYER, invited_by=None, now=past)
    users.insert(db, alice)
    for registration in (
        registrations.new_registration(league["_id"], bot["_id"], created_by=None, now=past),
        registrations.new_registration(
            league["_id"], user_id=alice["_id"], created_by=alice["_id"], now=past
        ),
    ):
        assert registrations.insert(db, registration)
    assert league_setup.start(db, league["_id"], past)
    return alice


def the_game(db) -> dict:
    (game,) = list(db[MATCHES].find({"type": matches.LEAGUE}))
    return game


def test_the_game_of_an_account_is_released_without_a_match_job(db, reference_bots, worker):
    league_with_account(db, reference_bots[0])

    worker.step()

    game = the_game(db)
    assert game["status"] == matches.QUEUED
    assert game["readiness"]["deadline"] - game["readiness"]["released_at"] == timedelta(hours=48)
    assert db[JOBS].count_documents({"payload.match_id": game["_id"]}) == 0


def test_a_ready_account_gets_a_play_job_for_the_play_runner(db, reference_bots, worker):
    alice = league_with_account(db, reference_bots[0])
    worker.step()
    game = the_game(db)
    color = competition_readiness.color_of(game, alice["_id"])
    _seat, seat_hash = play.new_seat()
    competition_readiness.mark_ready(db, game["_id"], color, seat_hash, utc_now())

    worker.step()

    job = db[JOBS].find_one({"payload.match_id": game["_id"]})
    assert (job["type"], job["status"]) == (jobs.PLAY, jobs.QUEUED)
    assert job["payload"]["competition"] is True
    assert the_game(db)["readiness"]["started_at"] is not None


def test_an_account_absent_at_the_deadline_loses_unplayed(db, reference_bots, config, worker):
    alice = league_with_account(db, reference_bots[0])
    worker.step()
    later = Worker(db, config, now=lambda: utc_now() + timedelta(hours=49), sleep=lambda _s: None)

    later.step()

    game = the_game(db)
    assert (game["status"], game["termination"]) == (matches.FINISHED, matches.FORFEIT_ABSENT)
    assert game["rated"] is False
    loser = competition_readiness.color_of(game, alice["_id"])
    assert game["result"] == ("0-1" if loser == "white" else "1-0")
