"""Lookup of API tokens by hash and per account (E116)."""

from pymongo import ASCENDING, IndexModel
from pymongo.database import Database

from sbm_store.names import API_TOKENS


def apply(db: Database) -> None:
    db[API_TOKENS].create_indexes(
        [
            IndexModel([("token_hash", ASCENDING)], unique=True),
            IndexModel([("user_id", ASCENDING), ("created_at", ASCENDING)]),
        ]
    )
