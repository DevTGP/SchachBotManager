"""Leagues, seasons and registrations (E131–E136); match jobs name their competition (E134)."""

from pymongo import ASCENDING, IndexModel
from pymongo.database import Database

from sbm_store import jobs
from sbm_store.names import JOBS, LEAGUES, MATCHES, REGISTRATIONS, SEASONS


def apply(db: Database) -> None:
    db[JOBS].update_many(
        {"type": jobs.MATCH, "competition": {"$exists": False}},
        {"$set": {"competition": jobs.SINGLE}},
    )
    db[JOBS].create_indexes([IndexModel([("competition", ASCENDING), ("claimed_at", ASCENDING)])])
    db[LEAGUES].create_indexes([IndexModel([("name_key", ASCENDING)], unique=True)])
    db[SEASONS].create_indexes(
        [
            IndexModel([("league_id", ASCENDING), ("number", ASCENDING)], unique=True),
            IndexModel([("status", ASCENDING)]),
        ]
    )
    db[REGISTRATIONS].create_indexes(
        [
            IndexModel(
                [("target_type", ASCENDING), ("target_id", ASCENDING), ("bot_id", ASCENDING)],
                unique=True,
                partialFilterExpression={"status": "active"},
            ),
            IndexModel([("bot_id", ASCENDING), ("status", ASCENDING)]),
        ]
    )
    db[MATCHES].create_indexes(
        [
            IndexModel(
                [
                    ("context.season_id", ASCENDING),
                    ("context.tier", ASCENDING),
                    ("status", ASCENDING),
                ],
                sparse=True,
            )
        ]
    )
