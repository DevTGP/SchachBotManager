"""Checking out an uploaded bot: its files as stored, or nothing at all."""

import os
import stat

import pytest
from sbm_store import bots
from sbm_store.names import BOTS
from uploads import GOOD, upload

from sbm_runner.checkout import CheckoutError, checkout


def files_in(path) -> dict[str, bytes]:
    return {
        file.relative_to(path).as_posix(): file.read_bytes()
        for file in path.rglob("*")
        if file.is_file()
    }


def test_the_files_land_as_uploaded(db, tmp_path):
    bot = upload(db)

    bot_dir = checkout(db, bot, tmp_path)

    assert bot_dir.temporary
    assert bot_dir.path.parent == tmp_path
    assert files_in(bot_dir.path) == {path: content for path, _kind, content in GOOD}
    bot_dir.remove()
    assert not bot_dir.path.exists()


@pytest.mark.skipif(os.name != "posix", reason="file modes are a POSIX matter")
def test_the_bot_may_read_but_not_write(db, tmp_path):
    bot_dir = checkout(db, upload(db), tmp_path)

    assert stat.S_IMODE(bot_dir.path.stat().st_mode) == 0o755
    assert stat.S_IMODE((bot_dir.path / "data").stat().st_mode) == 0o755
    assert stat.S_IMODE((bot_dir.path / "data" / "book.txt").stat().st_mode) == 0o644


def tamper(db, bot: dict, **changes) -> dict:
    files = [dict(entry) for entry in bot["files"]]
    files[0].update(changes)
    db[BOTS].update_one({"_id": bot["_id"]}, {"$set": {"files": files}})
    return bots.get(db, bot["_id"])


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"sha256": "0" * 64}, "hash"),
        ({"size": 1}, "hash"),
        ({"kind": "data"}, "path says source"),
        ({"path": "../escape.py"}, "stored path"),
        ({"path": "/etc/passwd.py"}, "stored path"),
    ],
)
def test_a_tampered_entry_leaves_nothing_behind(db, tmp_path, changes, message):
    bot = tamper(db, upload(db), **changes)

    with pytest.raises(CheckoutError, match=message):
        checkout(db, bot, tmp_path)

    assert list(tmp_path.iterdir()) == []


def test_a_path_twice_is_an_error(db, tmp_path):
    bot = upload(db)
    db[BOTS].update_one({"_id": bot["_id"]}, {"$push": {"files": bot["files"][0]}})

    with pytest.raises(FileExistsError):
        checkout(db, bots.get(db, bot["_id"]), tmp_path)

    assert list(tmp_path.iterdir()) == []
