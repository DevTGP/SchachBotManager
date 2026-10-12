"""Estimated start of a competition game whose accounts are ready (E187): the match runner starts
it in its next round, which comes once its current match is over (E183)."""

from datetime import datetime, timedelta

from pymongo.database import Database
from sbm_store import competition_readiness, jobs, matches

from sbm_api.queue_estimate import RecentDurations, schedule

# An idle runner looks for work every 2 s (RunnerConfig.poll_interval).
POLL = timedelta(seconds=2)


class StartEstimate:
    """The next round of the match runner, worked out once per request when first needed."""

    def __init__(self, db: Database, now: datetime) -> None:
        self._db = db
        self._now = now
        self._next_round: datetime | None = None

    def __call__(self, match: dict) -> datetime | None:
        """None unless the game waits for its start and every account is ready for it."""
        if not competition_readiness.waiting_for_ready(match):
            return None
        if not competition_readiness.startable(match["readiness"], self._now):
            return None
        if self._next_round is None:
            self._next_round = next_round(self._db, self._now)
        return self._next_round


def next_round(db: Database, now: datetime) -> datetime:
    """The runner takes its next round when the match it plays is over, by the same estimate as
    the queue (E20, E154); a running verification counts as over now."""
    running_jobs = jobs.running(db, jobs.MATCH)
    found = matches.summaries(db, [job["payload"]["match_id"] for job in running_jobs])
    running = list(found.values())
    times, _ = schedule(running, [], slots=0, now=now, duration=RecentDurations(db))
    return min((end for _, end in times), default=now) + POLL
