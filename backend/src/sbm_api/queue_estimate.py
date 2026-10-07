"""Estimated start and end times of queued matches (E20)."""

import heapq
from collections.abc import Callable
from datetime import datetime, timedelta

from pymongo.database import Database
from sbm_store import matches

RECENT_GAMES = 20
# Without history: both sides start, then a game uses about one side's initial time in total
# and gains the increment for about 40 moves per side.
ESTIMATED_MOVES_PER_GAME = 80

Duration = Callable[[dict], timedelta]


def fallback_duration(discipline: dict) -> timedelta:
    milliseconds = (
        2 * discipline["startup_ms"]
        + discipline["initial_time_ms"]
        + ESTIMATED_MOVES_PER_GAME * discipline["increment_ms"]
    )
    return timedelta(milliseconds=milliseconds)


class RecentDurations:
    """Average duration of the latest finished games of a discipline, cached per request."""

    def __init__(self, db: Database) -> None:
        self._db = db
        self._cache: dict[str, timedelta] = {}

    def __call__(self, discipline: dict) -> timedelta:
        name = discipline["name"]
        if name not in self._cache:
            recent = matches.recent_durations_ms(self._db, name, RECENT_GAMES)
            self._cache[name] = (
                timedelta(milliseconds=sum(recent) // len(recent))
                if recent
                else fallback_duration(discipline)
            )
        return self._cache[name]


def schedule(
    running: list[dict],
    waiting: list[tuple[dict, datetime]],
    *,
    slots: int,
    now: datetime,
    duration: Duration,
) -> tuple[list[tuple[datetime, datetime]], list[tuple[datetime, datetime]]]:
    """(start, end) for each running match and each waiting one with its earliest start.

    Waiting matches take the slot that frees up first, in queue order. A running match that
    takes longer than estimated ends "now", so the matches behind it do not start in the past.
    """
    running_times = []
    free = []
    for match in running:
        start = match["started_at"] or now
        end = max(now, start + duration(match["discipline_snapshot"]))
        running_times.append((start, end))
        free.append(end)
    free += [now] * max(0, slots - len(running))
    heapq.heapify(free)
    waiting_times = []
    for match, not_before in waiting:
        start = max(heapq.heappop(free), not_before, now)
        end = start + duration(match["discipline_snapshot"])
        heapq.heappush(free, end)
        waiting_times.append((start, end))
    return running_times, waiting_times
