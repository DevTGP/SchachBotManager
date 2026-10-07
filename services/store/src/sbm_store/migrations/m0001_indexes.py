"""Indexes for match lists, bot histories and the queue (datenmodell.md)."""

from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.database import Database

from sbm_store.names import BOTS, JOBS, MATCHES


def apply(db: Database) -> None:
    db[MATCHES].create_indexes(
        [
            IndexModel([("created_at", DESCENDING), ("_id", DESCENDING)]),
            IndexModel([("status", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("white.bot_id", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("black.bot_id", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel(
                [
                    ("status", ASCENDING),
                    ("discipline_snapshot.name", ASCENDING),
                    ("finished_at", DESCENDING),
                ]
            ),
        ]
    )
    db[JOBS].create_indexes(
        [
            IndexModel(
                [
                    ("type", ASCENDING),
                    ("status", ASCENDING),
                    ("priority", DESCENDING),
                    ("created_at", ASCENDING),
                    ("_id", ASCENDING),
                ]
            ),
            IndexModel([("status", ASCENDING), ("lease_until", ASCENDING)]),
        ]
    )
    db[BOTS].create_indexes(
        [
            IndexModel([("name", ASCENDING)]),
            IndexModel([("source_ref", ASCENDING)]),
        ]
    )
