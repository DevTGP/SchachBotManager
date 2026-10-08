"""The bots collection: one document per bot version (datenmodell.md, E6).

The reference bots have the source builtin:<module> (E72); uploaded bots keep their files in
GridFS (E82, bot_files.py). All versions with the same name form a lineage of one owner; the
name counts regardless of case through name_key, and (name_key, version_no) is unique (E91).
"""

from datetime import datetime

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from sbm_store.names import BOTS

SCHEMA_VERSION = 1
UPLOADED = "uploaded"
ANALYZING = "analyzing"
TESTING = "testing"
VERIFIED = "verified"
REJECTED = "rejected"
DISABLED = "disabled"
# Statuses of a bot that is still being verified.
PIPELINE = (UPLOADED, ANALYZING, TESTING)
# Statuses anyone may see; the others only the owner and admins.
PUBLIC = (VERIFIED, DISABLED)
BUILTIN_PREFIX = "builtin:"
GRIDFS = "gridfs"


def name_key(name: str) -> str:
    return name.lower()


def is_builtin(bot: dict) -> bool:
    return bot["source_ref"].startswith(BUILTIN_PREFIX)


def builtin_module(bot: dict) -> str | None:
    """The module name of a reference bot, None for any other bot."""
    if not is_builtin(bot):
        return None
    return bot["source_ref"].removeprefix(BUILTIN_PREFIX)


def new_uploaded_bot(
    *,
    bot_id: ObjectId,
    name: str,
    version: str,
    language: str,
    entry: str,
    files: list[dict],
    source_hash: str,
    owner_id: ObjectId,
    previous: dict | None,
    now: datetime,
) -> dict:
    """A new version after previous, the latest bot of the lineage, or the first one.

    files are the entries from bot_files.store_files, stored under bot_id.
    """
    return {
        "_id": bot_id,
        "schema_version": SCHEMA_VERSION,
        "name": name,
        "name_key": name_key(name),
        "version": version,
        "version_no": previous["version_no"] + 1 if previous else 1,
        "language": language,
        "owner_id": owner_id,
        "lineage_id": previous["lineage_id"] if previous else bot_id,
        "parent_bot_id": previous["_id"] if previous else None,
        "status": UPLOADED,
        "source_ref": GRIDFS,
        "entry": entry,
        "files": files,
        "source_hash": source_hash,
        "sizes": {
            kind: sum(file["size"] for file in files if file["kind"] == kind)
            for kind in sorted({file["kind"] for file in files})
        },
        "sdk_version": None,
        "runtime_version": None,
        "report_id": None,
        "rejection": None,
        "created_at": now,
        "verified_at": None,
        "rejected_at": None,
    }


def insert(db: Database, bot: dict) -> bool:
    """False if another upload took this version number of the name first."""
    try:
        db[BOTS].insert_one(bot)
    except DuplicateKeyError:
        return False
    return True


def get(db: Database, bot_id: ObjectId) -> dict | None:
    return db[BOTS].find_one({"_id": bot_id})


def latest(db: Database, name: str) -> dict | None:
    """The newest version with this name, regardless of case and status."""
    return db[BOTS].find_one({"name_key": name_key(name)}, sort=[("version_no", DESCENDING)])


def by_name(db: Database, name: str) -> dict | None:
    """The newest verified version with this name."""
    return db[BOTS].find_one(
        {"name_key": name_key(name), "status": VERIFIED}, sort=[("version_no", DESCENDING)]
    )


def all_by_name(db: Database) -> list[dict]:
    return list(db[BOTS].find().sort([("name_key", ASCENDING), ("version_no", ASCENDING)]))


def of_owner(db: Database, owner_id: ObjectId) -> list[dict]:
    """The bots of a user, newest first."""
    return list(
        db[BOTS]
        .find({"owner_id": owner_id})
        .sort([("created_at", DESCENDING), ("_id", DESCENDING)])
    )


def advance(db: Database, bot_id: ObjectId, status: str) -> bool:
    """Moves a bot to the next pipeline stage; False if it is no longer being verified."""
    result = db[BOTS].update_one(
        {"_id": bot_id, "status": {"$in": list(PIPELINE)}}, {"$set": {"status": status}}
    )
    return result.matched_count == 1


def finish_verification(
    db: Database,
    bot_id: ObjectId,
    *,
    verified: bool,
    report_id: ObjectId,
    rejection: dict | None,
    sdk_version: str | None,
    runtime_version: str | None,
    now: datetime,
) -> bool:
    """Ends the pipeline; rejection holds stage and reason. False if the bot already left it.

    The versions stay None if the runtime was not reached, e.g. after a server error.
    """
    fields = {
        "status": VERIFIED if verified else REJECTED,
        "report_id": report_id,
        "rejection": rejection,
        "sdk_version": sdk_version,
        "runtime_version": runtime_version,
        "verified_at" if verified else "rejected_at": now,
    }
    result = db[BOTS].update_one(
        {"_id": bot_id, "status": {"$in": list(PIPELINE)}}, {"$set": fields}
    )
    return result.matched_count == 1


def set_enabled(db: Database, bot_id: ObjectId, enabled: bool) -> dict | None:
    """Switches a bot between verified and disabled (E93); returns it as it is now.

    None if there is no such bot or it is in neither status.
    """
    return db[BOTS].find_one_and_update(
        {"_id": bot_id, "status": {"$in": [VERIFIED, DISABLED]}},
        {"$set": {"status": VERIFIED if enabled else DISABLED}},
        return_document=ReturnDocument.AFTER,
    )
