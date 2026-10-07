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
