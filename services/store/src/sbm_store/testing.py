"""pytest fixture `db`: a fresh database per test on the MongoDB from SBM_TEST_MONGO_URI.

Without a reachable server the tests that use it are skipped, unless SBM_REQUIRE_MONGO is set
as in CI, where they fail instead.
"""

import os
import uuid

import pytest
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from sbm_store.connection import connect

URI_VARIABLE = "SBM_TEST_MONGO_URI"
REQUIRE_VARIABLE = "SBM_REQUIRE_MONGO"
DEFAULT_URI = "mongodb://localhost:27017"
PROBE_TIMEOUT_MS = 1000
# The largest value MongoDB accepts; far beyond any test clock.
KEEP_SECONDS = 2**31 - 1


@pytest.fixture(scope="session")
def mongo_uri() -> str:
    uri = os.environ.get(URI_VARIABLE) or DEFAULT_URI
    probe = MongoClient(uri, serverSelectionTimeoutMS=PROBE_TIMEOUT_MS)
    try:
        probe.admin.command("ping")
    except PyMongoError as error:
        if os.environ.get(REQUIRE_VARIABLE):
            pytest.fail(f"MongoDB at {uri} is required but unreachable: {error}")
        pytest.skip(f"no MongoDB at {uri} (set {URI_VARIABLE})")
    finally:
        probe.close()
    return uri


@pytest.fixture
def db(mongo_uri: str):
    database = connect(mongo_uri, f"sbm_test_{uuid.uuid4().hex[:12]}")
    try:
        yield database
    finally:
        database.client.drop_database(database.name)
        database.client.close()


def keep_expired(database) -> None:
    """Stops the TTL indexes from removing documents of this database.

    Tests run on fixed clocks months before the real time, so MongoDB's TTL monitor would remove
    their sessions and links at a random moment within a minute.
    """
    for collection in database.list_collection_names():
        for name, index in database[collection].index_information().items():
            if "expireAfterSeconds" in index:
                database.command(
                    "collMod", collection, index={"name": name, "expireAfterSeconds": KEEP_SECONDS}
                )
