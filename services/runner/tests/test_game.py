from bson import ObjectId
from sbm_store import bots, jobs, matches, queue_settings
from sbm_store.names import BOTS, JOBS, MATCHES


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
