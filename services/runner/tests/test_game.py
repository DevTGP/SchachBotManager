from dataclasses import replace

from bson import ObjectId
from live_listener import LiveListener
from sbm_store import bots, jobs, matches, queue_settings, rating_recount, rating_values
from sbm_store.discipline import Discipline
from sbm_store.names import BOTS, JOBS, MATCHES
from sbm_store.rating_rule import DEFAULT, white_gain

from sbm_runner.worker import Worker, utc_now

START = DEFAULT.start

# As QUICK in conftest.py, but stored, so its games count. Not imported from conftest: the module
# name is shared with tests/sandbox/conftest.py, whose QUICK is referee settings.
RATED = Discipline(
    "Quick", initial_time_ms=10_000, increment_ms=0, max_moves=3, discipline_id=ObjectId()
)


def job_of(db, match_id: ObjectId) -> dict:
    return db[JOBS].find_one({"payload.match_id": match_id})


def test_plays_a_real_game_and_records_every_move(db, worker, reference_bots, enqueue):
    random, material = reference_bots
    match_id = enqueue(random, material)

    assert worker.step()

    match = matches.get(db, match_id)
    assert match["status"] == matches.FINISHED
    assert (match["result"], match["termination"]) == ("1/2-1/2", "max_moves")
    assert [move["ply"] for move in match["moves"]] == [1, 2, 3, 4, 5, 6]
    assert all(move["clock_ms"] <= 10_000 for move in match["moves"])
    assert match["white"]["sdk"] and match["white"]["lang"] == "python"
    assert match["black"]["lang"] == "python"
    assert match["started_at"] <= match["finished_at"]
    assert job_of(db, match_id)["status"] == jobs.DONE


def test_nothing_to_do_without_jobs(db, worker, reference_bots):
    assert not worker.step()


def test_paused_queue_keeps_the_job(db, worker, reference_bots, enqueue):
    match_id = enqueue(*reference_bots)
    queue_settings.set_paused(db, True)

    assert not worker.step()
    assert job_of(db, match_id)["status"] == jobs.QUEUED


def test_bot_needing_the_sandbox_aborts_the_match(db, worker, reference_bots, foreign_bot, enqueue):
    match_id = enqueue(reference_bots[0], foreign_bot)

    assert worker.step()

    match = matches.get(db, match_id)
    assert match["status"] == matches.ABORTED
    assert "sandbox" in match["termination_detail"]
    assert job_of(db, match_id)["status"] == jobs.FAILED


def test_bot_that_is_not_verified_aborts_the_match(db, worker, reference_bots, enqueue):
    random, material = reference_bots
    match_id = enqueue(random, material)
    db[BOTS].update_one({"_id": material["_id"]}, {"$set": {"status": bots.DISABLED}})

    assert worker.step()

    match = matches.get(db, match_id)
    assert match["status"] == matches.ABORTED
    assert match["termination_detail"].endswith("is disabled")
    assert job_of(db, match_id)["status"] == jobs.FAILED


def test_missing_bot_aborts_the_match(db, worker, reference_bots, enqueue):
    random, material = reference_bots
    match_id = enqueue(random, material)
    db[BOTS].delete_one({"_id": material["_id"]})

    assert worker.step()

    assert matches.get(db, match_id)["status"] == matches.ABORTED
    assert job_of(db, match_id)["status"] == jobs.FAILED


def test_finished_match_only_closes_its_job(db, worker, reference_bots, enqueue):
    match_id = enqueue(*reference_bots)
    db[MATCHES].update_one({"_id": match_id}, {"$set": {"status": matches.FINISHED}})

    assert worker.step()

    assert matches.get(db, match_id)["moves"] == []
    assert job_of(db, match_id)["status"] == jobs.DONE


def test_a_rated_match_moves_the_ratings_of_both_bots(db, worker, reference_bots, enqueue):
    random, material = reference_bots
    unrated = enqueue(random, material)
    rated = enqueue(random, material, RATED)

    assert worker.step()
    assert worker.step()

    assert "rating" not in matches.get(db, unrated)
    match = matches.get(db, rated)
    # Usually a draw after six plies; a quick mate by Random's blunders moves 50 points.
    gain = white_gain(START, START, match["result"], DEFAULT)
    assert match["rating"] == {
        "seq": 1,
        "white": {"before": START, "after": START + gain, "games": 1},
        "black": {"before": START, "after": START - gain, "games": 1},
    }
    assert rating_values.overall(bots.get(db, random["_id"]), START) == {
        "value": START + gain,
        "games": 1,
    }
    assert rating_values.overall(bots.get(db, material["_id"]), START) == {
        "value": START - gain,
        "games": 1,
    }


def test_ratings_are_counted_again_on_request_even_when_paused(db, worker, reference_bots, enqueue):
    random, material = reference_bots
    rated = enqueue(random, material, RATED)
    assert worker.step()
    db[MATCHES].delete_one({"_id": rated})
    rating_recount.request(db, utc_now())
    queue_settings.set_paused(db, True)

    assert not worker.step()

    assert not rating_recount.is_requested(db)
    for bot in (random, material):
        assert rating_values.overall(bots.get(db, bot["_id"]), START)["games"] == 0


def test_the_moves_go_live_to_the_gateway(db, config, reference_bots, enqueue):
    listener = LiveListener()
    try:
        live = replace(config, live_address=listener.address)
        worker = Worker(db, live, sleep=lambda _seconds: None)
        match_id = enqueue(*reference_bots)

        assert worker.step()
        listener.wait_closed()
    finally:
        listener.close()

    [lines] = listener.connections
    stored = matches.get(db, match_id)["moves"]
    assert lines[0] == {"type": "open", "v": 1, "match_id": str(match_id)}
    assert [line["move"]["uci"] for line in lines[1:-1]] == [move["uci"] for move in stored]
    assert [line["move"]["ply"] for line in lines[1:-1]] == [1, 2, 3, 4, 5, 6]
    assert lines[-1] == {"type": "end"}


def test_a_missing_gateway_does_not_stop_the_game(db, config, reference_bots, enqueue):
    listener = LiveListener()
    listener.close()
    worker = Worker(db, replace(config, live_address=listener.address), sleep=lambda _s: None)
    match_id = enqueue(*reference_bots)

    assert worker.step()

    assert matches.get(db, match_id)["status"] == matches.FINISHED
