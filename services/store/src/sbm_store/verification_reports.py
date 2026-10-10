"""The verification_reports collection: what the pipeline found for one bot (E92).

{bot_id, job_id, kind, started_at, finished_at, result, ruleset, runtime, stages: [{stage,
status, duration_ms, findings, tests}]}; the bot points to the report of its upload through
report_id. Rechecks by an admin (kind recheck, E153) only add reports; reports from before
E153 have no kind and count as upload reports.
"""

from datetime import datetime

from bson import ObjectId
from pymongo import DESCENDING
from pymongo.database import Database

from sbm_store.names import VERIFICATION_REPORTS

SCHEMA_VERSION = 1
PASSED = "passed"
FAILED = "failed"
# The stages a report can contain (verifikation.md); internal marks an error of the server.
ANALYSIS = "analysis"
TESTS = "tests"
INTERNAL = "internal"
UPLOAD = "upload"
RECHECK = "recheck"
# The bot page shows this many rechecks, newest first.
RECHECKS_SHOWN = 20


def new_report(
    *,
    bot_id: ObjectId,
    job_id: ObjectId,
    started_at: datetime,
    finished_at: datetime,
    passed: bool,
    ruleset: str | None,
    runtime: dict,
    stages: list[dict],
    kind: str = UPLOAD,
) -> dict:
    return {
        "_id": ObjectId(),
        "schema_version": SCHEMA_VERSION,
        "bot_id": bot_id,
        "job_id": job_id,
        "kind": kind,
        "started_at": started_at,
        "finished_at": finished_at,
        "result": PASSED if passed else FAILED,
        "ruleset": ruleset,
        "runtime": runtime,
        "stages": stages,
    }


def insert(db: Database, report: dict) -> None:
    db[VERIFICATION_REPORTS].insert_one(report)


def get(db: Database, report_id: ObjectId) -> dict | None:
    return db[VERIFICATION_REPORTS].find_one({"_id": report_id})


def rechecks_of(db: Database, bot_id: ObjectId) -> list[dict]:
    """The latest rechecks of a bot, newest first."""
    return list(
        db[VERIFICATION_REPORTS]
        .find({"bot_id": bot_id, "kind": RECHECK})
        .sort([("finished_at", DESCENDING), ("_id", DESCENDING)])
        .limit(RECHECKS_SHOWN)
    )
