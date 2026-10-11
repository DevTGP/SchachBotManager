"""Accounts in leagues and tournaments (E182–E184).

A registration names a bot or an account, so its unique index takes user_id as well; entries,
participants and match sides of accounts get indexes on user_id, released games one on their
readiness. Leagues and tournaments get ready_hours with its default.
"""

from pymongo import ASCENDING, IndexModel
from pymongo.database import Database

from sbm_store import leagues
from sbm_store.names import EDITIONS, LEAGUES, MATCHES, REGISTRATIONS, SEASONS, TOURNAMENTS

OLD_REGISTRATION_INDEX = "target_type_1_target_id_1_bot_id_1"


def apply(db: Database) -> None:
    db[REGISTRATIONS].update_many({"user_id": {"$exists": False}}, {"$set": {"user_id": None}})
    if OLD_REGISTRATION_INDEX in db[REGISTRATIONS].index_information():
        db[REGISTRATIONS].drop_index(OLD_REGISTRATION_INDEX)
    db[REGISTRATIONS].create_indexes(
        [
            IndexModel(
                [
                    ("target_type", ASCENDING),
                    ("target_id", ASCENDING),
                    ("bot_id", ASCENDING),
                    ("user_id", ASCENDING),
                ],
                unique=True,
                partialFilterExpression={"status": "active"},
            ),
            IndexModel([("user_id", ASCENDING), ("status", ASCENDING)]),
        ]
    )
    db[SEASONS].create_indexes([IndexModel([("tiers.entries.user_id", ASCENDING)])])
    db[EDITIONS].create_indexes([IndexModel([("participants.user_id", ASCENDING)])])
    db[MATCHES].create_indexes(
        [
            IndexModel([("white.user_id", ASCENDING), ("created_at", ASCENDING)], sparse=True),
            IndexModel([("black.user_id", ASCENDING), ("created_at", ASCENDING)], sparse=True),
            IndexModel(
                [("status", ASCENDING), ("readiness.started_at", ASCENDING)],
                partialFilterExpression={"readiness.deadline": {"$exists": True}},
            ),
        ]
    )
    default = leagues.DEFAULTS["ready_hours"]
    for collection in (LEAGUES, TOURNAMENTS):
        db[collection].update_many(
            {"ready_hours": {"$exists": False}}, {"$set": {"ready_hours": default}}
        )
