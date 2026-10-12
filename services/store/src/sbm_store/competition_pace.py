"""Pacing league and round robin games (E187): nobody gets more than one game ahead.

A group is a tier of a season or a round robin edition. Its current round is the earliest round
with a waiting or running game. Only the games of that round get jobs (between bots) or are
released (with an account); the next round follows once every game of the current one has ended,
played, forfeited or aborted. Each participant plays at most one game per round, so the fastest
is at most one game ahead of the slowest. Swiss and knockout pair round by round anyway and are
not paced here.
"""

from datetime import datetime

from pymongo.database import Database

from sbm_store import jobs, matches, tournaments
from sbm_store.names import JOBS, MATCHES

OPEN = {"status": {"$in": [matches.QUEUED, matches.RUNNING]}}


def group(context: dict) -> dict | None:
    """The filter of the game's group; None for a game that is not paced."""
    if "season_id" in context:
        return {"context.season_id": context["season_id"], "context.tier": context["tier"]}
    if context.get("format") == tournaments.ROUND_ROBIN:
        return {"context.edition_id": context["edition_id"]}
    return None


def current_round(db: Database, group_filter: dict) -> int | None:
    """The earliest round of the group with a waiting or running game; None if none is left."""
    found = db[MATCHES].find_one(
        group_filter | OPEN, {"context.round": 1}, sort=[("context.round", 1)]
    )
    return None if found is None else found["context"]["round"]


def due(db: Database, context: dict, cache: dict) -> bool:
    """Whether the game's round has come; cache keeps the current rounds of one pass."""
    found = group(context)
    if found is None:
        return True
    key = tuple(found.values())
    if key not in cache:
        cache[key] = current_round(db, found)
    return cache[key] is not None and context["round"] <= cache[key]


def add_round_jobs(
    db: Database, group_filter: dict, *, competition: str, priority: int, now: datetime
) -> int:
    """Jobs for the waiting bot games of the group's current round; returns how many."""
    round_number = current_round(db, group_filter)
    if round_number is None:
        return 0
    query = group_filter | {"context.round": round_number}
    return add_jobs(db, query, competition=competition, priority=priority, now=now)


def add_jobs(db: Database, query: dict, *, competition: str, priority: int, now: datetime) -> int:
    """Jobs for the waiting games between two bots that match query and have none; a game with
    an account waits for its readiness instead (E183). Returns how many."""
    waiting = [
        match["_id"]
        for match in db[MATCHES]
        .find(query | {"status": matches.QUEUED} | matches.BOTS_ONLY, {"_id": 1})
        .sort("_id", 1)
    ]
    if not waiting:
        return 0
    with_job = set(
        db[JOBS].distinct(
            "payload.match_id", {"type": jobs.MATCH, "payload.match_id": {"$in": waiting}}
        )
    )
    new = [
        jobs.new_match_job(match_id, priority=priority, now=now, competition=competition)
        for match_id in waiting
        if match_id not in with_job
    ]
    if new:
        db[JOBS].insert_many(new)
    return len(new)
