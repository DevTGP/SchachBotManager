"""Unique names for disciplines (E100)."""

from pymongo import ASCENDING, IndexModel
from pymongo.database import Database

from sbm_store.names import DISCIPLINES


def apply(db: Database) -> None:
    db[DISCIPLINES].create_indexes([IndexModel([("name_key", ASCENDING)], unique=True)])
