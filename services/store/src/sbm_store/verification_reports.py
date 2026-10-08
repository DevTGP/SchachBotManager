"""The verification_reports collection: what the pipeline found for one bot (E92).

{bot_id, job_id, started_at, finished_at, result, ruleset, runtime, stages: [{stage, status,
duration_ms, findings, tests}]}; the bot points to its report through report_id.
"""

from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store.names import VERIFICATION_REPORTS

SCHEMA_VERSION = 1
PASSED = "passed"
FAILED = "failed"
# The stages a report can contain (verifikation.md); internal marks an error of the server.
ANALYSIS = "analysis"
TESTS = "tests"
INTERNAL = "internal"


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
) -> dict:
    return {
        "_id": ObjectId(),
        "schema_version": SCHEMA_VERSION,
        "bot_id": bot_id,
        "job_id": job_id,
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
