"""Indexes for accounts, sessions, one-time links, the audit log and rate limits (E83–E85)."""

from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.database import Database

from sbm_store.names import AUDIT_LOG, INVITES, PASSWORD_RESETS, RATE_LIMITS, SESSIONS, USERS

# A TTL index with 0 s removes a document soon after its expires_at has passed.
EXPIRED = {"expireAfterSeconds": 0}


def apply(db: Database) -> None:
    db[USERS].create_indexes([IndexModel([("username_key", ASCENDING)], unique=True)])
    db[SESSIONS].create_indexes(
        [
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("expires_at", ASCENDING)], **EXPIRED),
        ]
    )
    db[INVITES].create_indexes(
        [
            IndexModel([("token_hash", ASCENDING)], unique=True),
            IndexModel([("expires_at", ASCENDING)], **EXPIRED),
            IndexModel([("used_at", ASCENDING), ("created_at", DESCENDING)]),
        ]
    )
    db[PASSWORD_RESETS].create_indexes(
        [
            IndexModel([("token_hash", ASCENDING)], unique=True),
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("expires_at", ASCENDING)], **EXPIRED),
        ]
    )
    db[AUDIT_LOG].create_indexes([IndexModel([("at", DESCENDING)])])
    db[RATE_LIMITS].create_indexes([IndexModel([("expires_at", ASCENDING)], **EXPIRED)])
