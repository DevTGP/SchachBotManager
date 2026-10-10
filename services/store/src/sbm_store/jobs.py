"""The jobs collection: the one queue for all work (datenmodell.md, A8, E20).

A worker claims a job atomically and holds it through a lease that it renews while it works.
A lease that runs out means the worker died; the job is then free for recovery.
"""

from datetime import datetime, timedelta

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.database import Database

from sbm_store.names import JOBS

SCHEMA_VERSION = 1
MATCH = "match"
# Checks an uploaded bot (E92); matches go first unless it waited too long (E89).
VERIFICATION = "verification"
VERIFICATION_PRIORITY = 0
QUEUED = "queued"
RUNNING = "running"
DONE = "done"
FAILED = "failed"
# Stopped by an admin (E152); the runner notices it when it renews the lease.
CANCELLED = "cancelled"

# Higher priority first, then first come, first served.
START_ORDER = [("priority", DESCENDING), ("created_at", ASCENDING), ("_id", ASCENDING)]


def new_match_job(match_id: ObjectId, *, priority: int, now: datetime) -> dict:
    return {
        "_id": ObjectId(),
        "schema_version": SCHEMA_VERSION,
        "type": MATCH,
        "payload": {"match_id": match_id},
        "priority": priority,
        "status": QUEUED,
        "not_before": now,
        "lease_until": None,
        "worker_id": None,
        "attempts": 0,
        "created_at": now,
        "finished_at": None,
    }


def new_verification_job(bot_id: ObjectId, *, now: datetime) -> dict:
    job = new_match_job(bot_id, priority=VERIFICATION_PRIORITY, now=now)
    job.update(type=VERIFICATION, payload={"bot_id": bot_id})
    return job


def new_recheck_job(bot_id: ObjectId, *, now: datetime) -> dict:
    """Checks a bot again for an admin; only writes a report, the status stays (E153)."""
    job = new_verification_job(bot_id, now=now)
    job["payload"]["recheck"] = True
    return job


def is_recheck(job: dict) -> bool:
    return job["payload"].get("recheck", False)


def insert(db: Database, job: dict) -> None:
    db[JOBS].insert_one(job)


def claim(
    db: Database,
    job_type: str,
    worker_id: str,
    *,
    now: datetime,
    lease: timedelta,
    created_before: datetime | None = None,
) -> dict | None:
    """Takes the next due job of a type, or returns None if there is none.

    With created_before only jobs queued before that time count.
    """
    query = {"type": job_type, "status": QUEUED, "not_before": {"$lte": now}}
    if created_before is not None:
        query["created_at"] = {"$lt": created_before}
    return db[JOBS].find_one_and_update(
        query,
        {
            "$set": {"status": RUNNING, "worker_id": worker_id, "lease_until": now + lease},
            "$inc": {"attempts": 1},
        },
        sort=START_ORDER,
        return_document=ReturnDocument.AFTER,
    )


def extend(db: Database, job_id: ObjectId, worker_id: str, until: datetime) -> bool:
    """Renews the lease; False if the worker no longer holds the job."""
    result = db[JOBS].update_one(
        {"_id": job_id, "status": RUNNING, "worker_id": worker_id},
        {"$set": {"lease_until": until}},
    )
    return result.matched_count == 1


def complete(db: Database, job_id: ObjectId, worker_id: str, now: datetime) -> None:
    _end(db, {"_id": job_id, "status": RUNNING, "worker_id": worker_id}, DONE, now)


def fail(db: Database, job_id: ObjectId, now: datetime) -> None:
    _end(db, {"_id": job_id, "status": {"$in": [QUEUED, RUNNING]}}, FAILED, now)


def _end(db: Database, query: dict, status: str, now: datetime) -> None:
    db[JOBS].update_one(
        query, {"$set": {"status": status, "lease_until": None, "finished_at": now}}
    )


def retry(db: Database, job_id: ObjectId, worker_id: str, not_before: datetime) -> None:
    """Hands a failed job back to the queue; it becomes due again at not_before."""
    db[JOBS].update_one(
        {"_id": job_id, "status": RUNNING, "worker_id": worker_id},
        {
            "$set": {
                "status": QUEUED,
                "worker_id": None,
                "lease_until": None,
                "not_before": not_before,
            }
        },
    )


def release(db: Database, job_id: ObjectId, worker_id: str) -> None:
    """Hands a job back unfinished on shutdown; that attempt does not count."""
    db[JOBS].update_one(
        {"_id": job_id, "status": RUNNING, "worker_id": worker_id},
        {
            "$set": {"status": QUEUED, "worker_id": None, "lease_until": None},
            "$inc": {"attempts": -1},
        },
    )


def expired(db: Database, job_type: str, now: datetime) -> list[dict]:
    return list(db[JOBS].find({"type": job_type, "status": RUNNING, "lease_until": {"$lt": now}}))


def requeue_expired(db: Database, job: dict) -> bool:
    """Frees a job whose lease ran out; False if someone else touched it in the meantime."""
    result = db[JOBS].update_one(
        {"_id": job["_id"], "status": RUNNING, "lease_until": job["lease_until"]},
        {"$set": {"status": QUEUED, "worker_id": None, "lease_until": None}},
    )
    return result.modified_count == 1


def fail_expired(db: Database, job: dict, now: datetime) -> bool:
    """Gives up a job whose lease ran out; False if someone else touched it in the meantime."""
    result = db[JOBS].update_one(
        {"_id": job["_id"], "status": RUNNING, "lease_until": job["lease_until"]},
        {"$set": {"status": FAILED, "lease_until": None, "finished_at": now}},
    )
    return result.modified_count == 1


def running(db: Database, job_type: str) -> list[dict]:
    return list(db[JOBS].find({"type": job_type, "status": RUNNING}).sort(START_ORDER))


def waiting(db: Database, job_type: str, limit: int) -> tuple[list[dict], int]:
    """The first queued jobs in start order, and how many are queued in total."""
    query = {"type": job_type, "status": QUEUED}
    items = list(db[JOBS].find(query).sort(START_ORDER).limit(limit))
    return items, db[JOBS].count_documents(query)


def cancel_match(
    db: Database, match_id: ObjectId, now: datetime, *, running: bool = True
) -> dict | None:
    """Cancels the queued or running job of a match; None if it has none (any more).

    running=False leaves a job alone that a runner has taken already (E157).
    """
    statuses = [QUEUED, RUNNING] if running else [QUEUED]
    return db[JOBS].find_one_and_update(
        {"type": MATCH, "payload.match_id": match_id, "status": {"$in": statuses}},
        {"$set": {"status": CANCELLED, "lease_until": None, "finished_at": now}},
    )


def set_match_priority(db: Database, match_id: ObjectId, priority: int) -> bool:
    """Changes the priority of a match's queued job; False if it is not queued (any more)."""
    result = db[JOBS].update_one(
        {"type": MATCH, "payload.match_id": match_id, "status": QUEUED},
        {"$set": {"priority": priority}},
    )
    return result.matched_count == 1


def verifying(db: Database, bot_id: ObjectId) -> bool:
    """Whether a verification of the bot is queued or running, a recheck included."""
    query = {"type": VERIFICATION, "payload.bot_id": bot_id, "status": {"$in": [QUEUED, RUNNING]}}
    return db[JOBS].count_documents(query, limit=1) > 0


def running_match(db: Database, match_id: ObjectId) -> bool:
    """Whether a runner holds the job of the match."""
    query = {"type": MATCH, "payload.match_id": match_id, "status": RUNNING}
    return db[JOBS].count_documents(query, limit=1) > 0


def running_verification(db: Database, bot_id: ObjectId) -> bool:
    query = {"type": VERIFICATION, "payload.bot_id": bot_id, "status": RUNNING}
    return db[JOBS].count_documents(query, limit=1) > 0
