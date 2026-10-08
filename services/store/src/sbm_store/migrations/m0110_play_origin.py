"""Indexes for the limits of interactive games (E115).

Only interactive matches have origin; the sparse indexes stay small.
"""

from pymongo import ASCENDING, IndexModel
from pymongo.database import Database

from sbm_store.names import MATCHES


def apply(db: Database) -> None:
    db[MATCHES].create_indexes(
        [
            IndexModel([(f"origin.{field}", ASCENDING)], sparse=True, name=f"origin_{field}")
            for field in ("ip_key", "user_id", "token_id")
        ]
    )
