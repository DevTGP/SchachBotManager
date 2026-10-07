import pytest

from sbm_store.connection import DEFAULT_DATABASE, database_from_env


def test_uri_is_required():
    with pytest.raises(RuntimeError, match="SBM_MONGO_URI"):
        database_from_env({})


def test_database_name_defaults():
    db = database_from_env({"SBM_MONGO_URI": "mongodb://localhost:1"})
    try:
        assert db.name == DEFAULT_DATABASE
    finally:
        db.client.close()
