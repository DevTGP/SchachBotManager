"""The invites collection: one-time links to create an account (E4, E83).

Redeeming claims the invite atomically first; if the account cannot be created after all, the
claim is released again. MongoDB removes expired invites through a TTL index.
"""

from datetime import datetime

from bson import ObjectId
from pymongo import DESCENDING
from pymongo.database import Database

from sbm_store.names import INVITES
from sbm_store.tokens import new_token, token_hash

SCHEMA_VERSION = 1


def create(
    db: Database,
    role: str,
    *,
    created_by: ObjectId | None,
    created_by_name: str | None,
    now: datetime,
    expires_at: datetime,
) -> tuple[dict, str]:
    """Returns the invite and its token, which is not stored."""
    token = new_token()
    invite = {
        "_id": ObjectId(),
        "schema_version": SCHEMA_VERSION,
        "token_hash": token_hash(token),
        "role": role,
        "created_by": created_by,
        "created_by_name": created_by_name,
        "created_at": now,
        "expires_at": expires_at,
        "used_at": None,
        "used_by": None,
    }
    db[INVITES].insert_one(invite)
    return invite, token


def open_invites(db: Database, now: datetime) -> list[dict]:
    """Unused and not expired, newest first."""
    query = {"used_at": None, "expires_at": {"$gt": now}}
    return list(db[INVITES].find(query).sort([("created_at", DESCENDING), ("_id", DESCENDING)]))


def revoke(db: Database, invite_id: ObjectId) -> bool:
    """Deletes an unused invite; False if there is none."""
    return db[INVITES].delete_one({"_id": invite_id, "used_at": None}).deleted_count == 1


def claim(db: Database, token: str, now: datetime) -> dict | None:
    """Marks a valid invite as used; None if the token is unknown, used or expired."""
    return db[INVITES].find_one_and_update(
        {"token_hash": token_hash(token), "used_at": None, "expires_at": {"$gt": now}},
        {"$set": {"used_at": now}},
    )


def release(db: Database, invite_id: ObjectId) -> None:
    db[INVITES].update_one({"_id": invite_id}, {"$set": {"used_at": None}})


def mark_used_by(db: Database, invite_id: ObjectId, user_id: ObjectId) -> None:
    db[INVITES].update_one({"_id": invite_id}, {"$set": {"used_by": user_id}})
