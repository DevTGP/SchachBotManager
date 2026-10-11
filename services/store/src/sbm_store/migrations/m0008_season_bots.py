"""The seasons of a bot are found by its lineup entries (E139)."""

from pymongo import ASCENDING, IndexModel
from pymongo.database import Database

from sbm_store.names import SEASONS


def apply(db: Database) -> None:
    db[SEASONS].create_indexes([IndexModel([("tiers.entries.bot_id", ASCENDING)])])
