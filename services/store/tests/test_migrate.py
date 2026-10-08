import pytest

from sbm_store import bots
from sbm_store.migrate import migrate
from sbm_store.migrations import MIGRATIONS
from sbm_store.names import BOTS, MATCHES, SESSIONS, USERS


def test_all_migrations_run_once(db):
    assert migrate(db) == [migration_id for migration_id, _ in MIGRATIONS]
    assert migrate(db) == []


def test_reference_bots_exist_once_after_a_repeated_migration(db):
    migrate(db)
    dict(MIGRATIONS)["0002_reference_bots"](db)

    found = sorted((bot["name"], bots.builtin_module(bot)) for bot in db[BOTS].find())
    assert found == [("Material", "material"), ("Random", "random_mover")]
    assert all(bot["status"] == bots.VERIFIED for bot in db[BOTS].find())


def test_indexes_exist(db):
    migrate(db)

    assert "white.bot_id_1_created_at_-1" in db[MATCHES].index_information()
    assert db[USERS].index_information()["username_key_1"]["unique"]
    assert db[SESSIONS].index_information()["expires_at_1"]["expireAfterSeconds"] == 0


def test_a_failed_migration_runs_again_next_time(db):
    calls = []

    def broken(_db):
        calls.append(1)
        raise RuntimeError("boom")

    for _ in range(2):
        with pytest.raises(RuntimeError):
            migrate(db, [("0001_broken", broken)])
    assert len(calls) == 2


def test_upload_indexes_exist(db):
    migrate(db)

    assert db[BOTS].index_information()["name_key_1_version_no_1"]["unique"]
    assert db["bot_files.chunks"].index_information()["files_id_1_n_1"]["unique"]
