"""Lookup of the job of a match, for cancelling it and changing its priority (E152)."""

from pymongo import ASCENDING, IndexModel
from pymongo.database import Database

from sbm_store.names import JOBS


def apply(db: Database) -> None:
    db[JOBS].create_indexes([IndexModel([("payload.match_id", ASCENDING)], sparse=True)])
