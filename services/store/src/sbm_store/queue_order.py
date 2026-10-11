"""The order in which the runner takes matches (E134).

The highest priority first; at the same priority the competition (a league, or all single
games) whose last match was taken longest ago, never taken first; within it the oldest match.
The runner claims by this rule and the queue view simulates it on the waiting jobs.
"""

from collections import deque
from collections.abc import Sequence
from datetime import datetime, timedelta

from pymongo.database import Database

from sbm_store import jobs
from sbm_store.names import JOBS

NEVER = (0,)


def competition(job: dict) -> str:
    return job.get("competition") or jobs.SINGLE


def last_claims(db: Database, competitions: Sequence[str]) -> dict[str, datetime]:
    """When a match of each competition was taken last; competitions without one are missing."""
    claims = {}
    for name in competitions:
        latest = db[JOBS].find_one(
            {"type": jobs.MATCH, "competition": name, "claimed_at": {"$exists": True}},
            {"claimed_at": 1},
            sort=[("claimed_at", -1)],
        )
        if latest is not None:
            claims[name] = latest["claimed_at"]
    return claims


def pick(candidates: Sequence[dict], claims: dict) -> dict:
    """The job to take among the first waiting job of each competition at one priority."""
    return min(candidates, key=lambda job: (_turn(claims, competition(job)), *_age(job)))


def order(waiting: Sequence[dict], claims: dict) -> list[dict]:
    """All waiting jobs in the order the runner would take them."""
    groups: dict[tuple, deque] = {}
    for job in sorted(waiting, key=lambda job: (-job["priority"], *_age(job))):
        groups.setdefault((job["priority"], competition(job)), deque()).append(job)
    turns = {name: (1, claimed) for name, claimed in claims.items()}
    result = []
    while groups:
        top = max(priority for priority, _ in groups)
        level = [key for key in groups if key[0] == top]
        key = min(level, key=lambda key: (turns.get(key[1], NEVER), *_age(groups[key][0])))
        result.append(groups[key].popleft())
        turns[key[1]] = (2, len(result))
        if not groups[key]:
            del groups[key]
    return result


def waiting(db: Database, limit: int) -> tuple[list[dict], int]:
    """The first queued match jobs in the order the runner takes them, and how many wait.

    Each competition contributes at most limit jobs, so the cut never hides one of them.
    """
    query = {"type": jobs.MATCH, "status": jobs.QUEUED}
    found = []
    # Migration 0007 gave every match job its competition.
    for name in db[JOBS].distinct("competition", query):
        scope = query | {"competition": name}
        found += db[JOBS].find(scope).sort(jobs.START_ORDER).limit(limit)
    claims = last_claims(db, sorted({competition(job) for job in found}))
    return order(found, claims)[:limit], db[JOBS].count_documents(query)


def claim_match(db: Database, worker_id: str, *, now: datetime, lease: timedelta) -> dict | None:
    """Takes the next due match job by this order; None if none is due."""
    due = {"type": jobs.MATCH, "status": jobs.QUEUED, "not_before": {"$lte": now}}
    while True:
        top = db[JOBS].find_one(due, sort=jobs.START_ORDER)
        if top is None:
            return None
        level = due | {"priority": top["priority"]}
        names = db[JOBS].distinct("competition", level)
        firsts = [
            db[JOBS].find_one(level | {"competition": name}, sort=jobs.START_ORDER)
            for name in names
        ]
        candidates = [job for job in firsts if job is not None] or [top]
        job = pick(candidates, last_claims(db, [competition(job) for job in candidates]))
        claimed = jobs.claim_job(db, job["_id"], worker_id, now=now, lease=lease)
        if claimed is not None:
            return claimed


def _turn(claims: dict, name: str) -> tuple:
    claimed = claims.get(name)
    return NEVER if claimed is None else (1, claimed)


def _age(job: dict) -> tuple:
    return job["created_at"], job["_id"]
