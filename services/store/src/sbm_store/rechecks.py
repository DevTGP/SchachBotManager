"""Rechecks: an admin has bots checked again with the current rules (E153).

A recheck is a verification job that only writes a report of kind recheck; the bot keeps its
status and its upload report. It waits like an upload (E89). A bot gets no second recheck
while a verification of it is still queued or running.
"""

from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import bots, jobs

# The statuses of a single bot that can be checked again; the others are still in the
# pipeline (E153).
RECHECKABLE = (bots.VERIFIED, bots.REJECTED, bots.DISABLED, bots.RETIRED)


def request(db: Database, bot_id: ObjectId, now: datetime) -> bool:
    """Queues a recheck of the bot; False if a verification of it is pending already."""
    if jobs.verifying(db, bot_id):
        return False
    jobs.insert(db, jobs.new_recheck_job(bot_id, now=now))
    return True


def request_language(db: Database, language: str, now: datetime) -> int:
    """Queues a recheck of every verified or rejected uploaded bot of a language.

    Returns how many it queued; bots with a pending verification are left out.
    """
    return sum(request(db, bot_id, now) for bot_id in bots.recheckable(db, language))
