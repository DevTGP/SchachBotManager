"""The bots collection: one document per bot version (datenmodell.md, E6).

Until M3 only the reference bots exist; their source is builtin:<module> (E72).
"""

from bson import ObjectId
from pymongo.database import Database

from sbm_store.names import BOTS

SCHEMA_VERSION = 1
VERIFIED = "verified"
BUILTIN_PREFIX = "builtin:"


def is_builtin(bot: dict) -> bool:
    return bot["source_ref"].startswith(BUILTIN_PREFIX)


def builtin_module(bot: dict) -> str | None:
    """The module name of a reference bot, None for any other bot."""
    if not is_builtin(bot):
        return None
    return bot["source_ref"].removeprefix(BUILTIN_PREFIX)


def get(db: Database, bot_id: ObjectId) -> dict | None:
    return db[BOTS].find_one({"_id": bot_id})


def by_name(db: Database, name: str) -> dict | None:
    return db[BOTS].find_one({"name": name})


def all_by_name(db: Database) -> list[dict]:
    return list(db[BOTS].find().sort([("name", 1), ("_id", 1)]))
