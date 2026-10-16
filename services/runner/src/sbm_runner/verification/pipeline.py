"""Verifies an uploaded bot: static analysis, build, the Mindesttests, then the report (E92).

Only C# has a build stage; sbm-build analyzes and compiles in one run (E203), and the program
goes into GridFS with the bot once it passes (E204). The bot's files are checked out once and
removed at the end; a bot that passes is verified at once (E93). A recheck by an admin runs the
same stages but only writes a report of kind recheck; the bot keeps its status and its program
(E153).
"""

import logging
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Protocol

from pymongo.database import Database
from sbm.analysis.upload import CSHARP
from sbm.referee import Player
from sbm_store import bot_files, bots, jobs, verification_reports
from sbm_store.verification_reports import FAILED, PASSED, RECHECK, TESTS, UPLOAD

from sbm_runner.checkout import BotDir, write_program
from sbm_runner.sandbox.run_once import Completed
from sbm_runner.verification.analysis_stage import ANALYSIS_SECONDS, analysis_stage
from sbm_runner.verification.build_stage import BUILD_SECONDS, build_stages
from sbm_runner.verification.minimum_tests import RANDOM, TEST_GAMES, play_test

log = logging.getLogger(__name__)


class Verifier(Protocol):
    """What the pipeline needs from the sandbox (sandbox/jail.py)."""

    # Per language the versions of its runtime and of the SDK, e.g. {"python": …, "sdk": …}.
    runtimes: dict[str, dict[str, str]]

    def checkout(self, bot: dict) -> BotDir: ...

    def analyze(self, bot_dir: Path, entry: str, timeout: float) -> Completed: ...

    def build(self, bot_dir: Path, entry: str, timeout: float) -> Completed: ...

    def candidate(self, bot: dict, bot_dir: Path, program_dir: Path | None) -> Player: ...

    def player(self, bot: dict) -> Player: ...


def run_verification(
    db: Database, job: dict, *, verifier: Verifier, now: Callable[[], datetime]
) -> None:
    """Exceptions are infrastructure errors; the caller retries or rejects the bot."""
    bot_id = job["payload"]["bot_id"]
    bot = bots.get(db, bot_id)
    if bot is None:
        log.error("job %s refers to the missing bot %s", job["_id"], bot_id)
        jobs.fail(db, job["_id"], now())
        return
    recheck = jobs.is_recheck(job)
    if not recheck and bot["status"] not in bots.PIPELINE:
        # The previous worker finished the bot but died before closing the job.
        jobs.complete(db, job["_id"], job["worker_id"], now())
        return
    log.info(
        "%s bot %s (%s %s)",
        "rechecking" if recheck else "verifying",
        bot_id,
        bot["name"],
        bot["version"],
    )
    started_at = now()
    bot_dir = verifier.checkout(bot)
    try:
        stages, ruleset, program = _stages(db, bot, verifier, bot_dir.path, advance=not recheck)
    finally:
        bot_dir.remove()
    runtime = verifier.runtimes.get(bot["language"], {})
    failed = next((stage for stage in stages if stage["status"] == FAILED), None)
    rejection = None if failed is None else {"stage": failed["stage"], "reason": failed["problem"]}
    report = verification_reports.new_report(
        bot_id=bot_id,
        job_id=job["_id"],
        started_at=started_at,
        finished_at=now(),
        passed=failed is None,
        ruleset=ruleset,
        runtime=runtime,
        stages=stages,
        kind=RECHECK if recheck else UPLOAD,
    )
    verification_reports.insert(db, report)
    if recheck:
        jobs.complete(db, job["_id"], job["worker_id"], now())
        log.info("bot %s rechecked: %s", bot_id, failed["problem"] if failed else "passed")
        return
    stored = None if program is None else bot_files.store_program(db, bot_id, program)
    finished = bots.finish_verification(
        db,
        bot_id,
        verified=failed is None,
        report_id=report["_id"],
        rejection=rejection,
        sdk_version=runtime.get("sdk"),
        runtime_version=_runtime_version(runtime),
        now=now(),
        program=stored,
    )
    if not finished and stored is not None:
        bot_files.delete_files(db, [stored])
    jobs.complete(db, job["_id"], job["worker_id"], now())
    log.info("bot %s: %s", bot_id, "verified" if failed is None else failed["problem"])


def _stages(
    db: Database, bot: dict, verifier: Verifier, bot_dir: Path, *, advance: bool
) -> tuple[list[dict], str | None, bytes | None]:
    """The stages, the ruleset and the program of a C# bot that passed them all.

    With advance the bot's status follows the stages; a recheck leaves it.
    """
    if advance:
        bots.advance(db, bot["_id"], bots.ANALYZING)
    start = time.monotonic()
    if bot["language"] == CSHARP:
        completed = verifier.build(bot_dir, bot["entry"], BUILD_SECONDS)
        stages, ruleset, program = build_stages(completed, _ms_since(start))
    else:
        completed = verifier.analyze(bot_dir, bot["entry"], ANALYSIS_SECONDS)
        analysis, ruleset = analysis_stage(completed, _ms_since(start))
        stages, program = [analysis], None
    if stages[-1]["status"] == FAILED:
        return stages, ruleset, None
    if advance:
        bots.advance(db, bot["_id"], bots.TESTING)
    if program is None:
        tests = _tests_stage(bot, verifier, bot_dir, None)
    else:
        # The program is mounted as /program, as in every game after this one.
        program_dir = write_program(bot_dir.parent, program)
        try:
            tests = _tests_stage(bot, verifier, bot_dir, program_dir.path)
        finally:
            program_dir.remove()
    passed = tests["status"] == PASSED
    return [*stages, tests], ruleset, program if passed else None


def _tests_stage(bot: dict, verifier: Verifier, bot_dir: Path, program_dir: Path | None) -> dict:
    """Stops at the first failed test; the server is too weak to play the rest for nothing."""
    start = time.monotonic()
    results = []
    for game in TEST_GAMES:
        player = verifier.candidate(bot, bot_dir, program_dir)
        results.append(play_test(game, player, verifier.player(RANDOM)))
        if not results[-1]["passed"]:
            break
    failed = next((result for result in results if not result["passed"]), None)
    return {
        "stage": TESTS,
        "status": PASSED if failed is None else FAILED,
        "duration_ms": _ms_since(start),
        "tests": results,
        "problem": None if failed is None else f"{failed['name']}: {failed['problem']}",
    }


def _runtime_version(runtime: dict[str, str]) -> str | None:
    """ "python 3.12.1" or "dotnet 10.0.13"; None if the runtime was not reached."""
    names = [name for name in runtime if name != "sdk"]
    return f"{names[0]} {runtime[names[0]]}" if len(names) == 1 else None


def _ms_since(start: float) -> int:
    return round((time.monotonic() - start) * 1000)
