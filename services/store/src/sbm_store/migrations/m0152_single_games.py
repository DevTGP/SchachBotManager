"""Lookups for series, the matches an account set and the matches of a discipline (E155, E156)."""

from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.database import Database

from sbm_store.names import MATCHES


def apply(db: Database) -> None:
    db[MATCHES].create_indexes(
        [
            IndexModel([("series.id", ASCENDING), ("series.index", ASCENDING)], sparse=True),
            IndexModel([("created_by", ASCENDING), ("created_at", DESCENDING)], sparse=True),
            IndexModel(
                [("discipline_snapshot.discipline_id", ASCENDING), ("created_at", DESCENDING)],
                sparse=True,
            ),
        ]
    )
