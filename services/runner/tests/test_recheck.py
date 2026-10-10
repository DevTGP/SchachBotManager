"""Rechecks by an admin (E153): the same stages, a report of kind recheck, the status stays."""

import pytest
from sbm_store import bots, jobs, rechecks, verification_reports
from sbm_store.names import JOBS
from sbm_store.verification_reports import ANALYSIS, FAILED, INTERNAL, PASSED, RECHECK, TESTS
from test_verification import lose_worker
from uploads import DIRTY, FakeVerifier, upload

from sbm_runner.recovery import recover_expired
from sbm_runner.worker import Worker, utc_now


@pytest.fixture
def verifier(db, tmp_path, reference_bots) -> FakeVerifier:
    return FakeVerifier(db, tmp_path)


@pytest.fixture
def verifying(db, config, verifier) -> Worker:
    return Worker(db, config, verifier=verifier, sleep=lambda _seconds: None)


def verified(db, verifying) -> dict:
    """An uploaded bot after its verification, with a recheck queued."""
    bot = upload(db)
    assert verifying.step()
    assert rechecks.request(db, bot["_id"], utc_now())
    return bots.get(db, bot["_id"])


def recheck_job(db, bot: dict) -> dict:
    return db[JOBS].find_one({"payload.bot_id": bot["_id"], "payload.recheck": True})


def only_recheck(db, bot: dict) -> dict:
    [report] = verification_reports.rechecks_of(db, bot["_id"])
    return report


def test_a_recheck_writes_its_own_report_and_keeps_the_bot(db, verifying, verifier):
    bot = verified(db, verifying)

    assert verifying.step()

    stored = bots.get(db, bot["_id"])
    assert stored == bot
    report = only_recheck(db, bot)
    assert (report["kind"], report["result"]) == (RECHECK, PASSED)
    assert [stage["stage"] for stage in report["stages"]] == [ANALYSIS, TESTS]
    assert verification_reports.get(db, bot["report_id"])["kind"] == verification_reports.UPLOAD
    assert recheck_job(db, bot)["status"] == jobs.DONE
    assert not verifier.checked_out[-1].path.exists()


def test_a_failed_recheck_does_not_reject_the_bot(db, verifying, verifier):
    bot = verified(db, verifying)
    verifier.report = DIRTY

    assert verifying.step()

    assert bots.get(db, bot["_id"])["status"] == bots.VERIFIED
    assert only_recheck(db, bot)["result"] == FAILED


def test_a_rejected_bot_can_pass_a_recheck_and_stays_rejected(db, verifying, verifier):
    verifier.report = DIRTY
    bot = upload(db)
    assert verifying.step()
    rechecks.request(db, bot["_id"], utc_now())
    verifier.report = {**DIRTY, "ok": True, "findings": []}

    assert verifying.step()

    assert bots.get(db, bot["_id"])["status"] == bots.REJECTED
    assert only_recheck(db, bot)["result"] == PASSED


def test_a_recheck_that_fails_too_often_only_writes_a_report(db, verifying, verifier):
    bot = verified(db, verifying)
    verifier.error = OSError("nsjail is gone")
    db[JOBS].update_one({"_id": recheck_job(db, bot)["_id"]}, {"$set": {"attempts": 2}})

    assert verifying.step()

    assert bots.get(db, bot["_id"]) == bot
    report = only_recheck(db, bot)
    assert [stage["stage"] for stage in report["stages"]] == [INTERNAL]
    assert recheck_job(db, bot)["status"] == jobs.FAILED


def test_a_recheck_lost_too_often_only_writes_a_report(db, config, verifying):
    bot = verified(db, verifying)
    db[JOBS].delete_many({"payload.recheck": {"$ne": True}})
    lose_worker(db, config, bot, attempts=config.max_attempts)

    assert recover_expired(db, config, utc_now()) == 1

    assert bots.get(db, bot["_id"]) == bot
    assert only_recheck(db, bot)["stages"][0]["stage"] == INTERNAL
