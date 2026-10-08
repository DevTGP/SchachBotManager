"""Ends the verification of a bot that the server could not check (E92).

After max_attempts failed attempts the bot is rejected with the stage internal; its owner can
upload it again. The details stay in the runner's log.
"""

from datetime import datetime

from pymongo.database import Database
from sbm_store import bots, verification_reports
from sbm_store.verification_reports import FAILED, INTERNAL


def reject_internal(db: Database, job: dict, attempts: int, now: datetime) -> None:
    """Writes the report and rejects the bot; the caller ends the job."""
    reason = f"the server could not verify the bot ({attempts} attempts)"
    report = verification_reports.new_report(
        bot_id=job["payload"]["bot_id"],
        job_id=job["_id"],
        started_at=now,
        finished_at=now,
        passed=False,
        ruleset=None,
        runtime={},
        stages=[{"stage": INTERNAL, "status": FAILED, "duration_ms": 0, "problem": reason}],
    )
    verification_reports.insert(db, report)
    bots.finish_verification(
        db,
        job["payload"]["bot_id"],
        verified=False,
        report_id=report["_id"],
        rejection={"stage": INTERNAL, "reason": reason},
        sdk_version=None,
        runtime_version=None,
        now=now,
    )
