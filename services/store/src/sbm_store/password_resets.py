"""The password_resets collection: one-time links from an admin to set a new password (E83).

A user has at most one valid link; a new one replaces the old. MongoDB removes expired links
through a TTL index.
"""

from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store.names import PASSWORD_RESETS
from sbm_store.tokens import new_token, token_hash


def create(
    db: Database,
    user_id: ObjectId,
    *,
    created_by: ObjectId | None,
    now: datetime,
    expires_at: datetime,
) -> tuple[dict, str]:
    """Returns the reset and its token, which is not stored."""
    db[PASSWORD_RESETS].delete_many({"user_id": user_id})
    token = new_token()
    reset = {
        "_id": ObjectId(),
        "token_hash": token_hash(token),
        "user_id": user_id,
        "created_by": created_by,
        "created_at": now,
        "expires_at": expires_at,
    }
    db[PASSWORD_RESETS].insert_one(reset)
    return reset, token


def redeem(db: Database, token: str, now: datetime) -> dict | None:
    """Removes a valid link and returns it; None if the token is unknown or expired."""
    return db[PASSWORD_RESETS].find_one_and_delete(
        {"token_hash": token_hash(token), "expires_at": {"$gt": now}}
    )
