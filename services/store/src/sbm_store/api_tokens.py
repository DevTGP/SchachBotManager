"""Personal API tokens: a coder's local bot plays against bots on the server with one (E116).

Only the hash of a token is stored; the token is shown once when it is made. A revoked token
stays as a record but no longer opens anything.
"""

from datetime import datetime

from bson import ObjectId
from pymongo import DESCENDING
from pymongo.database import Database

from sbm_store import tokens
from sbm_store.names import API_TOKENS

SCHEMA_VERSION = 1
# The prefix makes a leaked token recognizable, e.g. for secret scanners.
PREFIX = "sbm_"
MAX_PER_USER = 10


def new_token(user_id: ObjectId, name: str, *, now: datetime) -> tuple[str, dict]:
    """The token, shown once, and its document."""
    token = PREFIX + tokens.new_token()
    document = {
        "_id": ObjectId(),
        "schema_version": SCHEMA_VERSION,
        "user_id": user_id,
        "name": name,
        "token_hash": tokens.token_hash(token),
        "created_at": now,
        "last_used_at": None,
        "revoked_at": None,
    }
    return token, document


def insert(db: Database, document: dict) -> None:
    db[API_TOKENS].insert_one(document)


def active_of(db: Database, user_id: ObjectId) -> list[dict]:
    """Tokens not revoked, newest first."""
    query = {"user_id": user_id, "revoked_at": None}
    return list(db[API_TOKENS].find(query).sort("created_at", DESCENDING))


def revoke(db: Database, token_id: ObjectId, user_id: ObjectId, *, now: datetime) -> bool:
    """False if the account has no such active token."""
    result = db[API_TOKENS].update_one(
        {"_id": token_id, "user_id": user_id, "revoked_at": None},
        {"$set": {"revoked_at": now}},
    )
    return result.modified_count == 1


def find(db: Database, token: str, *, now: datetime) -> dict | None:
    """The active token document for a presented token; marks it used."""
    return db[API_TOKENS].find_one_and_update(
        {"token_hash": tokens.token_hash(token), "revoked_at": None},
        {"$set": {"last_used_at": now}},
    )
