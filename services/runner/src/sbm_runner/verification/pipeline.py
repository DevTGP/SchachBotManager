"""Verifies an uploaded bot: static analysis, then the Mindesttests, then the report (E92).

Python needs no build stage. The bot's files are checked out once and removed at the end;
a bot that passes is verified at once (E93). A recheck by an admin runs the same stages but
only writes a report of kind recheck; the bot keeps its status (E153).
"""

import logging
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Protocol

from pymongo.database import Database
from sbm.referee import Player
from sbm_store import bots, jobs, verification_reports
from sbm_store.verification_reports import FAILED, PASSED, RECHECK, TESTS, UPLOAD

from sbm_runner.checkout import BotDir
from sbm_runner.sandbox.run_once import Completed
from sbm_runner.verification.analysis_stage import ANALYSIS_SECONDS, analysis_stage
from sbm_runner.verification.minimum_tests import RANDOM, TEST_GAMES, play_test

log = logging.getLogger(__name__)


class Verifier(Protocol):
    """What the pipeline needs from the sandbox (sandbox/jail.py)."""

    runtime: dict[str, str]

    def checkout(self, bot: dict) -> BotDir: ...

    def analyze(self, bot_dir: Path, entry: str, timeout: float) -> Completed: ...

    def script_player(self, name: str, bot_dir: Path, script: str) -> Player: ...

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
        stages, ruleset = _stages(db, bot, verifier, bot_dir.path, advance=not recheck)
    finally:
        bot_dir.remove()
    failed = next((stage for stage in stages if stage["status"] == FAILED), None)
    rejection = None if failed is None else {"stage": failed["stage"], "reason": failed["problem"]}
    report = verification_reports.new_report(
        bot_id=bot_id,
        job_id=job["_id"],
        started_at=started_at,
        finished_at=now(),
        passed=failed is None,
        ruleset=ruleset,
        runtime=verifier.runtime,
        stages=stages,
        kind=RECHECK if recheck else UPLOAD,
    )
    verification_reports.insert(db, report)
    if recheck:
        jobs.complete(db, job["_id"], job["worker_id"], now())
        log.info("bot %s rechecked: %s", bot_id, failed["problem"] if failed else "passed")
        return
    bots.finish_verification(
        db,
        bot_id,
        verified=failed is None,
        report_id=report["_id"],
        rejection=rejection,
        sdk_version=verifier.runtime.get("sdk"),
        runtime_version=f"python {verifier.runtime['python']}" if verifier.runtime else None,
        now=now(),
    )
    jobs.complete(db, job["_id"], job["worker_id"], now())
    log.info("bot %s: %s", bot_id, "verified" if failed is None else failed["problem"])


def _stages(
    db: Database, bot: dict, verifier: Verifier, bot_dir: Path, *, advance: bool
) -> tuple[list[dict], str | None]:
    """With advance the bot's status follows the stages; a recheck leaves it."""
    if advance:
        bots.advance(db, bot["_id"], bots.ANALYZING)
    start = time.monotonic()
    completed = verifier.analyze(bot_dir, bot["entry"], ANALYSIS_SECONDS)
    analysis, ruleset = analysis_stage(completed, _ms_since(start))
    if analysis["status"] == FAILED:
        return [analysis], ruleset
    if advance:
        bots.advance(db, bot["_id"], bots.TESTING)
    return [analysis, _tests_stage(bot, verifier, bot_dir)], ruleset


def _tests_stage(bot: dict, verifier: Verifier, bot_dir: Path) -> dict:
    """Stops at the first failed test; the server is too weak to play the rest for nothing."""
    start = time.monotonic()
    results = []
    for game in TEST_GAMES:
        player = verifier.script_player(bot["name"], bot_dir, bot["entry"])
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


def _ms_since(start: float) -> int:
    return round((time.monotonic() - start) * 1000)
