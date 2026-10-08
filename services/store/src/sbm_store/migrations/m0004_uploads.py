"""Names, versions and indexes for uploaded bots, their files and reports (E91, E94)."""

from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.database import Database

from sbm_store import bots, versions
from sbm_store.names import BOT_FILES, BOTS, VERIFICATION_REPORTS


def apply(db: Database) -> None:
    for bot in db[BOTS].find({"name_key": {"$exists": False}}):
        db[BOTS].update_one(
            {"_id": bot["_id"]},
            {"$set": {"name_key": bots.name_key(bot["name"]), "version": versions.FIRST}},
        )
    db[BOTS].create_indexes(
        [
            IndexModel([("name_key", ASCENDING), ("version_no", ASCENDING)], unique=True),
            IndexModel([("owner_id", ASCENDING), ("created_at", DESCENDING)]),
        ]
    )
    db[VERIFICATION_REPORTS].create_indexes([IndexModel([("bot_id", ASCENDING)])])
    # The indexes GridFS would otherwise create on the first upload, which the api may not do.
    db[f"{BOT_FILES}.files"].create_indexes(
        [IndexModel([("filename", ASCENDING), ("uploadDate", ASCENDING)])]
    )
    db[f"{BOT_FILES}.chunks"].create_indexes(
        [IndexModel([("files_id", ASCENDING), ("n", ASCENDING)], unique=True)]
    )
