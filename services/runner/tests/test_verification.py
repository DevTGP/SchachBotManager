"""The verification of uploaded bots, with a fake sandbox; the jail itself is tested in sandbox/."""

from datetime import timedelta

import pytest
from sbm_store import bots, jobs, matches, queue_settings, verification_reports
from sbm_store.names import BOTS, JOBS
from sbm_store.verification_reports import ANALYSIS, FAILED, INTERNAL, PASSED, TESTS
from uploads import CRASHING, DIRTY, FINDING, FakeVerifier, upload

from sbm_runner.recovery import recover_expired
from sbm_runner.shutdown import Shutdown
from sbm_runner.verification.minimum_tests import TEST_GAMES
from sbm_runner.worker import Worker, utc_now


@pytest.fixture
def verifier(db, tmp_path, reference_bots) -> FakeVerifier:
    return FakeVerifier(db, tmp_path)


@pytest.fixture
def verifying(db, config, verifier) -> Worker:
    return Worker(db, config, verifier=verifier, sleep=lambda _seconds: None)


def job_of(db, bot: dict) -> dict:
    return db[JOBS].find_one({"payload.bot_id": bot["_id"]})


def report_of(db, bot: dict) -> dict:
    return verification_reports.get(db, bots.get(db, bot["_id"])["report_id"])


def test_a_bot_that_plays_by_the_rules_is_verified(db, verifying, verifier):
    bot = upload(db)

    assert verifying.step()

    stored = bots.get(db, bot["_id"])
    assert stored["status"] == bots.VERIFIED
    assert stored["verified_at"] is not None
    assert stored["rejection"] is None
    assert (stored["sdk_version"], stored["runtime_version"]) == ("0.4.0", "python 3.12.1")
    report = report_of(db, bot)
    assert (report["result"], report["ruleset"]) == (PASSED, "python-test")
    assert report["runtime"] == verifier.runtime
    assert [stage["stage"] for stage in report["stages"]] == [ANALYSIS, TESTS]
    tests = report["stages"][1]["tests"]
    assert [test["name"] for test in tests] == [game.name for game in TEST_GAMES]
    assert all(test["passed"] for test in tests)
    assert verifier.analyzed == ["bot.py", "data/book.txt", "helper.py"]
    assert not verifier.checked_out[0].path.exists()
    assert job_of(db, bot)["status"] == jobs.DONE


def test_findings_reject_the_bot_before_any_game(db, verifying, verifier):
    verifier.report = DIRTY
    bot = upload(db)

    assert verifying.step()

    stored = bots.get(db, bot["_id"])
    assert stored["status"] == bots.REJECTED
    assert stored["rejected_at"] is not None
    assert stored["rejection"] == {"stage": ANALYSIS, "reason": "1 problem found"}
    report = report_of(db, bot)
    assert report["result"] == FAILED
    assert [stage["stage"] for stage in report["stages"]] == [ANALYSIS]
    assert report["stages"][0]["findings"] == [FINDING]
    assert job_of(db, bot)["status"] == jobs.DONE


def test_a_failed_test_rejects_the_bot_and_stops_the_tests(db, verifying):
    bot = upload(db, CRASHING)

    assert verifying.step()

    stored = bots.get(db, bot["_id"])
    assert stored["status"] == bots.REJECTED
    assert stored["rejection"]["stage"] == TESTS
    assert stored["rejection"]["reason"].startswith(f"{TEST_GAMES[0].name}: ")
    tests = report_of(db, bot)["stages"][1]["tests"]
    assert len(tests) == 1
    assert not tests[0]["passed"]


def test_a_server_error_retries_the_verification_later(db, verifying, verifier):
    verifier.error = OSError("nsjail is gone")
    bot = upload(db)

    assert verifying.step()

    assert bots.get(db, bot["_id"])["status"] in bots.PIPELINE
    job = job_of(db, bot)
    assert job["status"] == jobs.QUEUED
    assert job["not_before"] > utc_now() + timedelta(seconds=20)
    assert not verifier.checked_out[0].path.exists()


def test_a_server_error_rejects_the_bot_after_the_last_attempt(db, verifying, verifier):
    verifier.error = OSError("nsjail is gone")
    bot = upload(db)
    db[JOBS].update_one({"_id": job_of(db, bot)["_id"]}, {"$set": {"attempts": 2}})

    assert verifying.step()

    stored = bots.get(db, bot["_id"])
    assert stored["status"] == bots.REJECTED
    assert stored["rejection"] == {
        "stage": INTERNAL,
        "reason": "the server could not verify the bot (3 attempts)",
    }
    assert (stored["sdk_version"], stored["runtime_version"]) == (None, None)
    assert "nsjail" not in str(report_of(db, bot))
    assert job_of(db, bot)["status"] == jobs.FAILED


def test_shutdown_hands_the_verification_back_without_counting(db, verifying, verifier):
    verifier.error = Shutdown("SIGTERM")
    bot = upload(db)

    with pytest.raises(Shutdown):
        verifying.step()

    job = job_of(db, bot)
    assert (job["status"], job["attempts"]) == (jobs.QUEUED, 0)
    assert bots.get(db, bot["_id"])["status"] in bots.PIPELINE


def test_a_missing_bot_fails_its_job(db, verifying):
    bot = upload(db)
    db[BOTS].delete_one({"_id": bot["_id"]})

    assert verifying.step()

    assert job_of(db, bot)["status"] == jobs.FAILED


def test_a_bot_that_left_the_pipeline_only_closes_its_job(db, verifying, verifier):
    bot = upload(db)
    db[BOTS].update_one({"_id": bot["_id"]}, {"$set": {"status": bots.REJECTED}})

    assert verifying.step()

    assert job_of(db, bot)["status"] == jobs.DONE
    assert verifier.checked_out == []


def test_matches_go_first(db, verifying, reference_bots, enqueue):
    bot = upload(db)
    match_id = enqueue(*reference_bots)

    assert verifying.step()

    assert matches.get(db, match_id)["status"] == matches.FINISHED
    assert job_of(db, bot)["status"] == jobs.QUEUED


def test_a_verification_that_waited_too_long_goes_first(db, verifying, reference_bots, enqueue):
    match_id = enqueue(*reference_bots)
    bot = upload(db)
    waited = utc_now() - timedelta(minutes=16)
    db[JOBS].update_one({"_id": job_of(db, bot)["_id"]}, {"$set": {"created_at": waited}})

    assert verifying.step()

    assert bots.get(db, bot["_id"])["status"] == bots.VERIFIED
    assert matches.get(db, match_id)["status"] == matches.QUEUED


def test_a_verification_runs_when_no_match_waits(db, verifying):
    bot = upload(db)

    assert verifying.step()

    assert job_of(db, bot)["status"] == jobs.DONE


def test_without_sandbox_nothing_is_verified(db, worker, reference_bots):
    bot = upload(db)

    assert not worker.step()

    assert job_of(db, bot)["status"] == jobs.QUEUED


def test_a_paused_queue_holds_verifications_too(db, verifying):
    bot = upload(db)
    queue_settings.set_paused(db, True)

    assert not verifying.step()

    assert job_of(db, bot)["status"] == jobs.QUEUED


def lose_worker(db, config, bot: dict, *, attempts: int) -> None:
    """A worker claimed the verification and vanished; its lease ran out long ago."""
    db[JOBS].update_one({"_id": job_of(db, bot)["_id"]}, {"$set": {"attempts": attempts - 1}})
    past = utc_now() - timedelta(minutes=10)
    jobs.claim(db, jobs.VERIFICATION, "dead-worker", now=past, lease=config.lease)


def test_a_lost_verification_starts_over(db, config, verifier):
    bot = upload(db)
    lose_worker(db, config, bot, attempts=1)

    assert recover_expired(db, config, utc_now()) == 1

    assert job_of(db, bot)["status"] == jobs.QUEUED


def test_a_verification_lost_too_often_rejects_the_bot(db, config, verifier):
    bot = upload(db)
    lose_worker(db, config, bot, attempts=config.max_attempts)

    assert recover_expired(db, config, utc_now()) == 1

    stored = bots.get(db, bot["_id"])
    assert stored["status"] == bots.REJECTED
    assert stored["rejection"]["stage"] == INTERNAL
    assert job_of(db, bot)["status"] == jobs.FAILED
