"""Lookup of the verification jobs of a bot, for rechecks (E153)."""

from pymongo import ASCENDING, IndexModel
from pymongo.database import Database

from sbm_store.names import JOBS


def apply(db: Database) -> None:
    db[JOBS].create_indexes([IndexModel([("payload.bot_id", ASCENDING)], sparse=True)])
