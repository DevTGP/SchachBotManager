"""Connection to MongoDB from the environment; the URI carries the user of each service."""

import os
from datetime import UTC

from pymongo import MongoClient
from pymongo.database import Database

URI_VARIABLE = "SBM_MONGO_URI"
DATABASE_VARIABLE = "SBM_MONGO_DB"
DEFAULT_DATABASE = "sbm"
SERVER_SELECTION_TIMEOUT_MS = 5000


def connect(uri: str, name: str) -> Database:
    """Datetimes come back timezone-aware in UTC."""
    client = MongoClient(
        uri,
        tz_aware=True,
        tzinfo=UTC,
        serverSelectionTimeoutMS=SERVER_SELECTION_TIMEOUT_MS,
        appname="sbm",
    )
    return client[name]


def database_from_env(environ: dict[str, str] = os.environ) -> Database:
    uri = environ.get(URI_VARIABLE)
    if not uri:
        raise RuntimeError(f"{URI_VARIABLE} is not set")
    return connect(uri, environ.get(DATABASE_VARIABLE) or DEFAULT_DATABASE)
