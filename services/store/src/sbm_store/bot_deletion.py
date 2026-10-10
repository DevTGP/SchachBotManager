"""Deleting one version of a bot for good, by an admin (E105).

Goes with the bot: its files, its verification reports and jobs, and every match it played
with that match's job. If one of those matches was counted, the runner counts all ratings
again (rating_recount). The name is free again once no version is left (bots.latest).

Without transactions the steps run in an order a crash can repeat: the bot document goes
last, so a second attempt finds it and removes what is left. Reference bots, bots still being
verified, bots in a running recheck (E153) and bots in a running match cannot be deleted.
"""

from dataclasses import dataclass
from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import bot_files, bots, jobs, matches, rating_recount
from sbm_store.names import BOTS, JOBS, MATCHES, VERIFICATION_REPORTS

BUILTIN = "builtin"
VERIFYING = "verifying"
PLAYING = "playing"


class NotDeletable(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class Deletion:
    bot: dict
    matches: int
    recount: bool


def delete_bot(db: Database, bot_id: ObjectId, now: datetime) -> Deletion | None:
    """Deletes the bot and all that belongs to it; None if there is no such bot."""
    bot = bots.get(db, bot_id)
    if bot is None:
        return None
    _check(db, bot)
    played = matches.match_filter(bot_id=bot_id)
    match_ids = [match["_id"] for match in db[MATCHES].find(played, {"_id": 1})]
    recount = db[MATCHES].count_documents({**played, "rating": {"$exists": True}}) > 0
    if recount:
        # Asked before and after: a crash in between still leaves a request behind.
        rating_recount.request(db, now)
    db[JOBS].delete_many(
        {
            "$or": [
                {"type": jobs.MATCH, "payload.match_id": {"$in": match_ids}},
                {"type": jobs.VERIFICATION, "payload.bot_id": bot_id},
            ]
        }
    )
    db[MATCHES].delete_many({"_id": {"$in": match_ids}})
    if recount:
        rating_recount.request(db, now)
    db[VERIFICATION_REPORTS].delete_many({"bot_id": bot_id})
    bot_files.delete_files(db, bot.get("files", []))
    db[BOTS].update_many(
        {"parent_bot_id": bot_id}, {"$set": {"parent_bot_id": bot.get("parent_bot_id")}}
    )
    db[BOTS].delete_one({"_id": bot_id})
    return Deletion(bot=bot, matches=len(match_ids), recount=recount)


def _check(db: Database, bot: dict) -> None:
    if bots.is_builtin(bot):
        raise NotDeletable(BUILTIN)
    if bot["status"] in bots.PIPELINE or jobs.running_verification(db, bot["_id"]):
        raise NotDeletable(VERIFYING)
    running = matches.match_filter(status=matches.RUNNING, bot_id=bot["_id"])
    if db[MATCHES].count_documents(running, limit=1) > 0:
        raise NotDeletable(PLAYING)
