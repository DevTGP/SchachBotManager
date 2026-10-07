"""The users collection: accounts with one role, no email (E83).

Usernames are unique regardless of case through username_key. Accounts are deactivated, never
deleted, so their bots and matches stay consistent (datenmodell.md).
"""

from datetime import datetime

from bson import ObjectId
from pymongo import ASCENDING, ReturnDocument
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from sbm_store.names import USERS

SCHEMA_VERSION = 1
CODER = "coder"
ADMIN = "admin"
ROLES = (CODER, ADMIN)


def username_key(username: str) -> str:
    return username.lower()


def new_user(
    username: str,
    password_hash: str,
    role: str,
    *,
    invited_by: ObjectId | None,
    now: datetime,
) -> dict:
    return {
        "_id": ObjectId(),
        "schema_version": SCHEMA_VERSION,
        "username": username,
        "username_key": username_key(username),
        "password_hash": password_hash,
        "role": role,
        "active": True,
        "invited_by": invited_by,
        "failed_logins": 0,
        "locked_until": None,
        "created_at": now,
        "last_login_at": None,
    }


def insert(db: Database, user: dict) -> bool:
    """False if the username is taken."""
    try:
        db[USERS].insert_one(user)
    except DuplicateKeyError:
        return False
    return True


def get(db: Database, user_id: ObjectId) -> dict | None:
    return db[USERS].find_one({"_id": user_id})


def by_username(db: Database, username: str) -> dict | None:
    return db[USERS].find_one({"username_key": username_key(username)})


def username_taken(db: Database, username: str) -> bool:
    return db[USERS].count_documents({"username_key": username_key(username)}, limit=1) > 0


def all_by_name(db: Database) -> list[dict]:
    return list(db[USERS].find().sort([("username_key", ASCENDING)]))


def update(db: Database, user_id: ObjectId, fields: dict) -> dict | None:
    """Sets role and/or active; returns the user as it is now, None if there is none."""
    return db[USERS].find_one_and_update(
        {"_id": user_id}, {"$set": fields}, return_document=ReturnDocument.AFTER
    )


def set_password_hash(db: Database, user_id: ObjectId, password_hash: str) -> None:
    db[USERS].update_one({"_id": user_id}, {"$set": {"password_hash": password_hash}})


def record_login(db: Database, user_id: ObjectId, now: datetime) -> None:
    db[USERS].update_one(
        {"_id": user_id},
        {"$set": {"last_login_at": now, "failed_logins": 0, "locked_until": None}},
    )


def count_failed_login(db: Database, user_id: ObjectId) -> int:
    """Counts a wrong password; returns the failures since the last login or lock."""
    user = db[USERS].find_one_and_update(
        {"_id": user_id},
        {"$inc": {"failed_logins": 1}},
        projection={"failed_logins": 1},
        return_document=ReturnDocument.AFTER,
    )
    return user["failed_logins"] if user else 0


def lock(db: Database, user_id: ObjectId, until: datetime) -> None:
    db[USERS].update_one({"_id": user_id}, {"$set": {"locked_until": until, "failed_logins": 0}})
