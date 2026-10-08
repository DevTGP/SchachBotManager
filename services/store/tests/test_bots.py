from bson import ObjectId
from conftest import T0

from sbm_store import bots
from sbm_store.migrate import migrate

OWNER = ObjectId()
FILES = [
    {"path": "bot.py", "kind": "source", "size": 10, "sha256": "a", "file_id": ObjectId()},
    {"path": "data/book.txt", "kind": "data", "size": 4, "sha256": "b", "file_id": ObjectId()},
]


def upload(db, name="Alpha", version="1.0.0", *, owner=OWNER, now=T0) -> dict:
    bot = bots.new_uploaded_bot(
        bot_id=ObjectId(),
        name=name,
        version=version,
        language="python",
        entry="bot.py",
        files=FILES,
        source_hash="h",
        owner_id=owner,
        previous=bots.latest(db, name),
        now=now,
    )
    assert bots.insert(db, bot)
    return bot


def test_first_version_starts_a_lineage(db):
    migrate(db)
    bot = upload(db)

    assert bot["version_no"] == 1
    assert bot["lineage_id"] == bot["_id"]
    assert bot["parent_bot_id"] is None
    assert bot["status"] == bots.UPLOADED
    assert bot["sizes"] == {"data": 4, "source": 10}
    assert not bots.is_builtin(bot)


def test_next_version_continues_the_lineage(db):
    migrate(db)
    first = upload(db)
    second = upload(db, "ALPHA", "1.0.1")

    assert second["version_no"] == 2
    assert second["lineage_id"] == first["_id"]
    assert second["parent_bot_id"] == first["_id"]
    assert bots.latest(db, "alpha")["_id"] == second["_id"]


def test_a_version_number_is_taken_once(db):
    migrate(db)
    upload(db)
    rival = bots.new_uploaded_bot(
        bot_id=ObjectId(),
        name="alpha",
        version="2.0.0",
        language="python",
        entry="bot.py",
        files=FILES,
        source_hash="h",
        owner_id=ObjectId(),
        previous=None,
        now=T0,
    )

    assert not bots.insert(db, rival)


def test_reference_bots_have_names_and_versions(db):
    migrate(db)

    random = bots.latest(db, "random")
    assert random["version"] == "1.0.0"
    assert random["owner_id"] is None
    assert bots.by_name(db, "RANDOM")["_id"] == random["_id"]


def test_by_name_takes_the_newest_verified_version(db):
    migrate(db)
    first = upload(db)
    upload(db, version="1.1.0")

    assert bots.by_name(db, "Alpha") is None
    bots.finish_verification(
        db,
        first["_id"],
        verified=True,
        report_id=ObjectId(),
        rejection=None,
        sdk_version="0.4.0",
        runtime_version="3.12",
        now=T0,
    )
    assert bots.by_name(db, "Alpha")["_id"] == first["_id"]


def test_of_owner_lists_newest_first(db):
    migrate(db)
    first = upload(db)
    second = upload(db, "Beta", now=T0.replace(hour=13))
    upload(db, "Gamma", owner=ObjectId())

    assert [bot["_id"] for bot in bots.of_owner(db, OWNER)] == [second["_id"], first["_id"]]


def test_pipeline_moves_forward_until_it_ends(db):
    migrate(db)
    bot = upload(db)

    assert bots.advance(db, bot["_id"], bots.ANALYZING)
    report_id = ObjectId()
    rejection = {"stage": "analysis", "reason": "import os is not allowed"}
    assert bots.finish_verification(
        db,
        bot["_id"],
        verified=False,
        report_id=report_id,
        rejection=rejection,
        sdk_version="0.4.0",
        runtime_version="3.12",
        now=T0,
    )

    stored = bots.get(db, bot["_id"])
    assert stored["status"] == bots.REJECTED
    assert stored["rejection"] == rejection
    assert stored["report_id"] == report_id
    assert stored["rejected_at"] == T0
    assert stored["verified_at"] is None
    assert not bots.advance(db, bot["_id"], bots.TESTING)


def test_only_verified_and_disabled_bots_switch(db):
    migrate(db)
    bot = upload(db)

    assert bots.set_enabled(db, bot["_id"], False) is None
    random = bots.latest(db, "Random")
    assert bots.set_enabled(db, random["_id"], False)["status"] == bots.DISABLED
    assert bots.set_enabled(db, random["_id"], True)["status"] == bots.VERIFIED
