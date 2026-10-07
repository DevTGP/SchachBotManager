"""The sessions collection: one document per login, keyed by the hash of the cookie (E84).

MongoDB removes expired sessions through a TTL index; until it runs, find ignores them.
"""

from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store.names import SESSIONS
from sbm_store.tokens import new_token, token_hash


def create(db: Database, user_id: ObjectId, *, now: datetime, expires_at: datetime) -> str:
    """Returns the token for the cookie."""
    token = new_token()
    db[SESSIONS].insert_one(
        {
            "_id": token_hash(token),
            "user_id": user_id,
            "created_at": now,
            "expires_at": expires_at,
        }
    )
    return token


def find(db: Database, token: str, now: datetime) -> dict | None:
    return db[SESSIONS].find_one({"_id": token_hash(token), "expires_at": {"$gt": now}})


def extend(db: Database, session_id: str, expires_at: datetime) -> None:
    db[SESSIONS].update_one({"_id": session_id}, {"$set": {"expires_at": expires_at}})


def delete(db: Database, token: str) -> None:
    db[SESSIONS].delete_one({"_id": token_hash(token)})


def delete_for_user(db: Database, user_id: ObjectId, *, keep: str | None = None) -> None:
    """Ends every session of a user, except the one with the id keep."""
    query: dict = {"user_id": user_id}
    if keep is not None:
        query["_id"] = {"$ne": keep}
    db[SESSIONS].delete_many(query)
