"""The verification of C# bots with a fake build (E203, E204): the program goes into GridFS."""

import base64

import pytest
from sbm_store import bot_files, bots, rechecks, verification_reports
from sbm_store.verification_reports import ANALYSIS, BUILD, FAILED, PASSED, TESTS
from uploads import CRASHING, NOT_BUILT, PROGRAM, FakeVerifier, upload_csharp

from sbm_runner.checkout import checkout
from sbm_runner.worker import Worker, utc_now


@pytest.fixture
def verifier(db, tmp_path, reference_bots) -> FakeVerifier:
    return FakeVerifier(db, tmp_path / "checkouts")


@pytest.fixture
def verifying(db, config, verifier) -> Worker:
    return Worker(db, config, verifier=verifier, sleep=lambda _seconds: None)


def report_of(db, bot: dict) -> dict:
    return verification_reports.get(db, bots.get(db, bot["_id"])["report_id"])


def test_a_compiled_bot_is_verified_with_its_program(db, verifying, verifier, tmp_path):
    bot = upload_csharp(db)

    assert verifying.step()

    stored = bots.get(db, bot["_id"])
    assert stored["status"] == bots.VERIFIED
    assert (stored["sdk_version"], stored["runtime_version"]) == ("0.4.0", "dotnet 10.0.13")
    assert bot_files.read_file(db, stored["program"]) == PROGRAM
    report = report_of(db, bot)
    assert (report["result"], report["ruleset"]) == (PASSED, "csharp-test")
    assert report["runtime"] == verifier.runtimes["csharp"]
    assert [stage["stage"] for stage in report["stages"]] == [ANALYSIS, BUILD, TESTS]
    assert verifier.analyzed == ["MyBot.cs", "data/book.txt"]
    # The tests played the new program from a directory of its own, removed afterwards.
    assert len(set(verifier.programs)) == 1
    assert not verifier.programs[0].exists()
    assert not verifier.checked_out[0].path.exists()
    # Every game after this one gets the stored program next to the files.
    bot_dir = checkout(db, stored, tmp_path / "game")
    assert (bot_dir.program.path / bot_files.PROGRAM).read_bytes() == PROGRAM
    bot_dir.remove()
    assert list((tmp_path / "game").iterdir()) == []


def test_errors_of_the_compiler_reject_the_bot_before_any_game(db, verifying, verifier):
    verifier.built = NOT_BUILT
    bot = upload_csharp(db)

    assert verifying.step()

    stored = bots.get(db, bot["_id"])
    assert stored["status"] == bots.REJECTED
    assert stored["rejection"] == {"stage": BUILD, "reason": "1 problem found"}
    assert stored["program"] is None
    assert [stage["stage"] for stage in report_of(db, bot)["stages"]] == [ANALYSIS, BUILD]
    assert verifier.programs == []


def test_a_program_that_fails_the_tests_is_not_kept(db, verifying, verifier):
    verifier.built = {**verifier.built, "program": _base64(CRASHING[0][2])}
    bot = upload_csharp(db)

    assert verifying.step()

    stored = bots.get(db, bot["_id"])
    assert (stored["status"], stored["rejection"]["stage"]) == (bots.REJECTED, TESTS)
    assert stored["program"] is None
    assert report_of(db, bot)["stages"][-1]["status"] == FAILED
    assert not list(bot_files.bucket(db).find({"metadata.program": True}))


def test_a_recheck_keeps_the_program(db, verifying, verifier):
    bot = upload_csharp(db)
    assert verifying.step()
    program = bots.get(db, bot["_id"])["program"]
    assert rechecks.request(db, bot["_id"], utc_now())
    verifier.built = {**verifier.built, "program": _base64(b"other")}

    assert verifying.step()

    assert bots.get(db, bot["_id"])["program"] == program
    assert len(list(bot_files.bucket(db).find({"metadata.program": True}))) == 1


def _base64(content: bytes) -> str:
    return base64.b64encode(content).decode()
