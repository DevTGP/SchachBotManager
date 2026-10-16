"""League and tournament games with an account in the play runner (E185)."""

import time
from datetime import timedelta

from bson import ObjectId
from conftest import Person
from sbm_store import competition_readiness, jobs, matches, play, play_settings
from sbm_store.discipline import Discipline
from sbm_store.names import JOBS

from sbm_runner.play.config import PlayConfig
from sbm_runner.play.worker import recover_expired_play, utc_now

QUICK = Discipline("Quick", initial_time_ms=10_000, increment_ms=0, max_moves=3)
SHORT = Discipline("Short", initial_time_ms=500, increment_ms=0, max_moves=3)


def wait_for(predicate, seconds: float = 15) -> None:
    deadline = time.monotonic() + seconds
    while not predicate():
        assert time.monotonic() < deadline, "timed out"
        time.sleep(0.05)


def started_league_game(db, bot: dict, discipline: Discipline = QUICK) -> tuple:
    """A released league game of alice with white against the bot, ready and started as the
    match runner does it; returns match id and alice's seat."""
    now = utc_now() - timedelta(minutes=1)
    alice = {"_id": ObjectId(), "user_id": ObjectId(), "name": "alice"}
    context = {"season_id": ObjectId(), "tier": 1, "round": 1, "board": 1}
    match = matches.new_league_match(alice, bot, discipline, context=context, priority=0, now=now)
    match["readiness"] = competition_readiness.new_readiness(match, now, 48)
    matches.insert(db, match)
    seat, seat_hash = play.new_seat()
    assert competition_readiness.mark_ready(db, match["_id"], "white", seat_hash, utc_now())
    assert competition_readiness.start_ready(db, utc_now()) == [match["_id"]]
    return match["_id"], seat


def job_of(db, match_id) -> dict:
    return db[JOBS].find_one({"payload.match_id": match_id})


def waiting_again(db, match_id) -> bool:
    match = matches.get(db, match_id)
    return match["status"] == matches.QUEUED and match["readiness"]["started_at"] is None


def assert_reset(db, match_id) -> None:
    match = matches.get(db, match_id)
    assert (match["status"], match["moves"]) == (matches.QUEUED, [])
    assert match["readiness"]["white"] == {"ready_at": None, "seen_at": None}
    assert match["white"]["seat_hash"] is None
    assert job_of(db, match_id)["status"] == jobs.FAILED


def test_a_person_plays_a_league_game(db, gateway, play_worker, reference_bots):
    match_id, seat = started_league_game(db, reference_bots[0])
    person = Person(gateway.url, match_id, seat)
    person.start()

    assert play_worker.step()
    wait_for(lambda: matches.get(db, match_id)["status"] == matches.FINISHED)
    person.join(10)

    match = matches.get(db, match_id)
    assert (match["result"], match["termination"]) == ("1/2-1/2", "max_moves")
    assert job_of(db, match_id)["status"] == jobs.DONE


def test_the_game_starts_without_an_absent_person_whose_clock_runs_out(
    db, make_play_worker, gateway, play_config, reference_bots
):
    config = PlayConfig(**{**play_config.__dict__, "connect_wait": timedelta(seconds=0.5)})
    worker = make_play_worker(config)
    match_id, _seat = started_league_game(db, reference_bots[0], SHORT)

    assert worker.step()
    wait_for(lambda: matches.get(db, match_id)["status"] == matches.FINISHED)

    match = matches.get(db, match_id)
    assert (match["result"], match["termination"]) == ("0-1", "timeout")


def test_an_unreachable_gateway_resets_the_game(
    db, make_play_worker, play_config, gateway, reference_bots
):
    config = PlayConfig(**{**play_config.__dict__, "relay_port": 1})
    worker = make_play_worker(config)
    match_id, _seat = started_league_game(db, reference_bots[0])

    assert worker.step()
    wait_for(lambda: waiting_again(db, match_id))
    wait_for(lambda: job_of(db, match_id)["status"] == jobs.FAILED)

    assert_reset(db, match_id)


def test_a_competition_job_that_lost_its_runner_resets_the_game(db, reference_bots):
    match_id, _seat = started_league_game(db, reference_bots[0])
    claimed = jobs.claim(db, play.PLAY_JOB, "dead", now=utc_now(), lease=timedelta(seconds=1))
    assert claimed is not None

    assert recover_expired_play(db, utc_now() + timedelta(seconds=5)) == 1

    assert_reset(db, match_id)


def test_competition_games_start_beyond_the_limit_of_the_website(
    db, make_play_worker, gateway, play_config, reference_bots, create_remote
):
    play_settings.save(db, play_settings.PlaySettings(max_games=1))
    config = PlayConfig(**{**play_config.__dict__, "slots": 2})
    worker = make_play_worker(config)
    first, _ = create_remote()
    second, _ = create_remote()
    league_game, _seat = started_league_game(db, reference_bots[0])

    assert worker.step()
    assert worker.step()
    assert not worker.step()

    assert job_of(db, first)["status"] == jobs.RUNNING
    assert job_of(db, second)["status"] == jobs.QUEUED
    assert job_of(db, league_game)["status"] == jobs.RUNNING
    worker.stop()
    assert matches.get(db, first)["status"] == matches.ABORTED
    assert waiting_again(db, league_game)
