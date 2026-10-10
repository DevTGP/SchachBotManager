"""The queue as the API shows it (schema Queue): match jobs joined with their matches, and the
interactive games under way (E119)."""

from datetime import datetime

from pymongo.database import Database
from sbm_store import jobs, matches, play, queue_settings

from sbm_api.match_view import match_summary
from sbm_api.queue_estimate import RecentDurations, schedule
from sbm_api.timestamps import timestamp

MAX_WAITING = 200


def queue_view(db: Database, now: datetime) -> dict:
    settings = queue_settings.get(db)
    running_jobs = jobs.running(db, jobs.MATCH)
    waiting_jobs, waiting_total = jobs.waiting(db, jobs.MATCH, MAX_WAITING)
    found = matches.summaries(
        db, [job["payload"]["match_id"] for job in running_jobs + waiting_jobs]
    )
    # A job whose match is gone fails when the runner reaches it; the queue skips it.
    running = [found[job["payload"]["match_id"]] for job in running_jobs if _has_match(job, found)]
    waiting = [
        (found[job["payload"]["match_id"]], job["not_before"])
        for job in waiting_jobs
        if _has_match(job, found)
    ]
    # The job decides the order; interactive games have none of their own and show 0 (E152).
    priorities = {
        job["payload"]["match_id"]: job["priority"] for job in running_jobs + waiting_jobs
    }
    duration = RecentDurations(db)
    running_times, waiting_times = schedule(
        running, waiting, slots=settings.parallelism, now=now, duration=duration
    )
    # Interactive games have their own runner: they are shown but take no slot (E119).
    interactive = play.running_summaries(db)
    interactive_times, _ = schedule(interactive, [], slots=0, now=now, duration=duration)
    return {
        "paused": settings.paused,
        "running": [
            _entry(match, 0, times, priorities.get(match["_id"], 0))
            for match, times in zip(
                running + interactive, running_times + interactive_times, strict=True
            )
        ],
        "waiting": [
            _entry(match, position, times, priorities[match["_id"]])
            for position, ((match, _), times) in enumerate(
                zip(waiting, waiting_times, strict=True), start=1
            )
        ],
        "waiting_total": waiting_total,
    }


def _has_match(job: dict, found: dict) -> bool:
    return job["payload"]["match_id"] in found


def _entry(match: dict, position: int, times: tuple[datetime, datetime], priority: int) -> dict:
    start, end = times
    return {
        "match": match_summary(match),
        "position": position,
        "priority": priority,
        "estimated_start": timestamp(start),
        "estimated_end": timestamp(end),
    }
