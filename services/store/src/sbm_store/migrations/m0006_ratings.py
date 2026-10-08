"""Indexes for ratings (E103): one number per counted match, bots ordered by rating."""

from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.database import Database

from sbm_store.names import BOTS, MATCHES


def apply(db: Database) -> None:
    db[MATCHES].create_indexes(
        [
            IndexModel(
                [("rating.seq", ASCENDING)],
                unique=True,
                partialFilterExpression={"rating.seq": {"$exists": True}},
            ),
            IndexModel([("status", ASCENDING), ("rated", ASCENDING), ("finished_at", ASCENDING)]),
        ]
    )
    db[BOTS].create_indexes([IndexModel([("rating.value", DESCENDING)])])
