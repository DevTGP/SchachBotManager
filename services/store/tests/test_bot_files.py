from bson import ObjectId

from sbm_store import bot_files

FILES = [("bot.py", "source", b"print(1)\n"), ("data/book.txt", "data", b"e4\n")]


def test_files_are_stored_and_read_back(db):
    bot_id = ObjectId()
    entries = bot_files.store_files(db, bot_id, FILES)

    assert [(entry["path"], entry["kind"], entry["size"]) for entry in entries] == [
        ("bot.py", "source", 9),
        ("data/book.txt", "data", 3),
    ]
    assert [bot_files.read_file(db, entry) for entry in entries] == [b"print(1)\n", b"e4\n"]
    stored = db["bot_files.files"].find_one({"_id": entries[0]["file_id"]})
    assert stored["metadata"] == {"bot_id": bot_id, "path": "bot.py"}


def test_deleted_files_are_gone(db):
    entries = bot_files.store_files(db, ObjectId(), FILES)

    bot_files.delete_files(db, entries)
    bot_files.delete_files(db, entries)

    assert db["bot_files.files"].count_documents({}) == 0
    assert db["bot_files.chunks"].count_documents({}) == 0


def test_source_hash_ignores_order_and_sees_content():
    a = {"path": "a.py", "sha256": "1"}
    b = {"path": "b.py", "sha256": "2"}

    assert bot_files.source_hash([a, b]) == bot_files.source_hash([b, a])
    assert bot_files.source_hash([a, b]) != bot_files.source_hash([a, {**b, "sha256": "3"}])
