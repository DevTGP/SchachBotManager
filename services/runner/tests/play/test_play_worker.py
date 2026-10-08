import time
from datetime import timedelta

from conftest import RemoteBot
from sbm_store import jobs, matches, play
from sbm_store.names import JOBS

from sbm_runner.play.config import PlayConfig
from sbm_runner.play.worker import PlayWorker, recover_expired_play, utc_now


def wait_for(predicate, seconds: float = 15) -> None:
    deadline = time.monotonic() + seconds
    while not predicate():
        assert time.monotonic() < deadline, "timed out"
        time.sleep(0.05)


def finished(db, match_id) -> bool:
    return matches.get(db, match_id)["status"] in (matches.FINISHED, matches.ABORTED)


def job_of(db, match_id) -> dict:
    return db[JOBS].find_one({"payload.match_id": match_id})


def test_a_remote_bot_plays_a_whole_game_through_the_gateway(
    db, gateway, play_worker, create_remote
):
    match_id, seat = create_remote()
    remote = RemoteBot(gateway.url, match_id, seat)
    remote.start()

    assert play_worker.step()
    wait_for(lambda: finished(db, match_id))
    remote.join(10)

    match = matches.get(db, match_id)
    assert match["status"] == matches.FINISHED
    assert (match["result"], match["termination"]) == ("1/2-1/2", "max_moves")
    assert len(match["moves"]) == 6
    assert (match["white"]["sdk"], match["white"]["lang"]) == ("0.1.0", "python")
    assert match["rated"] is False
    assert remote.types()[:2] == ["joined", "init"]
    assert remote.types()[-1] == "game_over"
    assert job_of(db, match_id)["status"] == jobs.DONE


def test_a_seat_nobody_takes_aborts_the_match(db, gateway, play_config, create_remote):
    config = PlayConfig(**{**play_config.__dict__, "connect_wait": timedelta(seconds=0.5)})
    worker = PlayWorker(db, config, sleep=lambda _seconds: None)
    match_id, _seat = create_remote()

    assert worker.step()
    wait_for(lambda: finished(db, match_id))

    match = matches.get(db, match_id)
    assert (match["status"], match["result"]) == (matches.ABORTED, "*")
    assert "did not connect" in match["termination_detail"]
    assert job_of(db, match_id)["status"] == jobs.FAILED


def test_a_client_that_leaves_for_good_aborts_the_game(db, gateway, play_worker, create_remote):
    match_id, seat = create_remote()
    remote = RemoteBot(gateway.url, match_id, seat, leave_after=1)
    remote.start()

    assert play_worker.step()
    wait_for(lambda: finished(db, match_id))

    match = matches.get(db, match_id)
    assert match["status"] == matches.ABORTED
    assert "SeatAbandoned" in match["termination_detail"]


def test_people_cannot_play_before_step_2(db, gateway, play_worker, create_remote):
    match_id, _seat = create_remote(play.HUMAN)

    assert play_worker.step()
    wait_for(lambda: finished(db, match_id))

    assert "cannot play yet" in matches.get(db, match_id)["termination_detail"]


def test_an_unreachable_gateway_aborts_the_match(db, play_config, create_remote, gateway):
    config = PlayConfig(**{**play_config.__dict__, "relay_port": 1})
    worker = PlayWorker(db, config, sleep=lambda _seconds: None)
    match_id, _seat = create_remote()

    assert worker.step()
    wait_for(lambda: finished(db, match_id))

    assert matches.get(db, match_id)["status"] == matches.ABORTED


def test_slots_limit_the_games_at_once(db, gateway, play_worker, create_remote):
    first, _ = create_remote()
    second, _ = create_remote()

    assert play_worker.step()
    assert not play_worker.step()
    assert play_worker.running == 1
    assert job_of(db, second)["status"] == jobs.QUEUED
    wait_for(lambda: finished(db, first))
    play_worker.stop()


def test_stop_aborts_running_games(db, gateway, play_worker, create_remote):
    match_id, seat = create_remote()
    remote = RemoteBot(gateway.url, match_id, seat, delay=1.0)
    remote.start()
    assert play_worker.step()
    wait_for(lambda: matches.get(db, match_id)["status"] != matches.QUEUED)

    play_worker.stop()

    assert matches.get(db, match_id)["status"] == matches.ABORTED
    assert play_worker.running == 0


def test_a_play_job_that_lost_its_runner_is_given_up(db, create_remote):
    match_id, _seat = create_remote()
    claimed = jobs.claim(db, play.PLAY_JOB, "dead", now=utc_now(), lease=timedelta(seconds=1))
    assert claimed is not None

    assert recover_expired_play(db, utc_now() + timedelta(seconds=5)) == 1

    assert matches.get(db, match_id)["status"] == matches.ABORTED
    assert job_of(db, match_id)["status"] == jobs.FAILED


def test_a_match_left_running_is_not_restarted(db, gateway, play_worker, create_remote):
    match_id, _seat = create_remote()
    matches.start(db, match_id, utc_now())

    assert play_worker.step()
    wait_for(lambda: finished(db, match_id))

    assert "cannot be resumed" in matches.get(db, match_id)["termination_detail"]
