"""GET /bots/{bot_id}/file and /bots/{bot_id}/source: files for owner and admins (E97)."""

import io
import zipfile

from bson import ObjectId

from bot_uploads import BOT, store_bot, verify

FILES = (
    ("bot.py", "source", BOT),
    ("lib/helper.py", "source", b"X = 1\n"),
    ("data/book.bin", "data", b"\x00\xff"),
)


def get_file(client, bot, path):
    return client.get(f"/api/v1/bots/{bot['_id']}/file", query_string={"path": path})


def test_the_owner_downloads_one_file(login, db):
    coder, user = login()
    bot = store_bot(db, user["_id"], files=FILES)

    response = get_file(coder, bot, "lib/helper.py")

    assert response.status_code == 200
    assert response.data == b"X = 1\n"
    assert response.mimetype == "application/octet-stream"
    assert response.headers["Content-Disposition"] == 'attachment; filename="helper.py"'
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Cache-Control"] == "private, no-store"


def test_an_unknown_or_missing_path(login, db):
    coder, user = login()
    bot = store_bot(db, user["_id"], files=FILES)

    assert get_file(coder, bot, "lib").status_code == 404
    assert get_file(coder, bot, "x" * 201).status_code == 400
    response = coder.get(f"/api/v1/bots/{bot['_id']}/file")
    assert (response.status_code, response.json["field"]) == (400, "path")


def test_the_source_is_a_zip_file_with_a_folder(login, db):
    coder, user = login()
    bot = store_bot(db, user["_id"], name="Sharp", version="1.2.3", files=FILES)

    response = coder.get(f"/api/v1/bots/{bot['_id']}/source")

    assert response.status_code == 200
    assert response.mimetype == "application/zip"
    assert response.headers["Content-Disposition"] == 'attachment; filename="Sharp-1.2.3.zip"'
    with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
        assert archive.namelist() == [
            "Sharp-1.2.3/bot.py",
            "Sharp-1.2.3/data/book.bin",
            "Sharp-1.2.3/lib/helper.py",
        ]
        assert archive.read("Sharp-1.2.3/data/book.bin") == b"\x00\xff"
        assert {info.date_time for info in archive.infolist()} == {(1980, 1, 1, 0, 0, 0)}
    # The same files give the same bytes.
    assert coder.get(f"/api/v1/bots/{bot['_id']}/source").data == response.data


def test_admins_read_any_files(admin, db):
    bot = verify(db, store_bot(db, ObjectId(), files=FILES))
    assert admin.get(f"/api/v1/bots/{bot['_id']}/source").status_code == 200
    assert get_file(admin, bot, "bot.py").data == BOT


def test_reference_bots_have_no_files(admin, reference_bots):
    response = admin.get(f"/api/v1/bots/{reference_bots[0]['_id']}/source")
    assert response.status_code == 404


def test_only_owner_and_admins(client, login, db):
    other, _ = login("other")
    _, user = login()
    public = verify(db, store_bot(db, user["_id"]))
    hidden = store_bot(db, user["_id"], name="Hidden")

    for route in ("source", "file?path=bot.py"):
        assert client.get(f"/api/v1/bots/{public['_id']}/{route}").status_code == 401
        assert other.get(f"/api/v1/bots/{public['_id']}/{route}").status_code == 403
        assert other.get(f"/api/v1/bots/{hidden['_id']}/{route}").status_code == 404
        assert other.get(f"/api/v1/bots/{ObjectId()}/{route}").status_code == 404
