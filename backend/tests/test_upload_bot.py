"""POST /bots: upload as source files, checked by the SDK's rules, verified later (E91, E92)."""

from datetime import timedelta

import pytest
from bson import ObjectId
from sbm_store import bot_files, bots, jobs
from sbm_store.names import BOT_FILES, BOTS, JOBS

from sbm_api import rate_limit

from accounts import CSRF
from bot_uploads import FILES, post_upload, store_bot, upload_form


def test_the_upload_waits_for_its_verification(login, db):
    coder, user = login()

    response = post_upload(coder)

    assert response.status_code == 201
    view = response.json
    assert (view["name"], view["version"], view["status"]) == ("Sharp", "1.0.0", "uploaded")
    assert view["builtin"] is False
    assert view["details"]["owner"] == "coder"
    assert view["details"]["entry"] == "bot.py"
    assert view["details"]["files"] == [
        {"path": "bot.py", "kind": "source", "size": len(FILES["bot.py"])},
        {"path": "helper.py", "kind": "source", "size": 6},
        {"path": "data/book.txt", "kind": "data", "size": 5},
    ]
    assert view["details"]["report"] is None
    bot = bots.get(db, ObjectId(view["id"]))
    assert (bot["owner_id"], bot["version_no"], bot["lineage_id"]) == (user["_id"], 1, bot["_id"])
    assert {entry["path"]: bot_files.read_file(db, entry) for entry in bot["files"]} == FILES
    job = db[JOBS].find_one()
    assert (job["type"], job["payload"]["bot_id"]) == (jobs.VERIFICATION, bot["_id"])


def test_the_same_name_makes_a_new_version(login, db, clock):
    coder, user = login()
    first = store_bot(db, user["_id"])
    clock.advance(timedelta(minutes=1))

    response = post_upload(coder, name="sharp", version="1.0.1")

    assert response.status_code == 201
    bot = bots.get(db, ObjectId(response.json["id"]))
    assert (bot["version_no"], bot["lineage_id"], bot["parent_bot_id"]) == (
        2,
        first["_id"],
        first["_id"],
    )


@pytest.mark.parametrize("version", ["1.0.0", "0.9.9"])
def test_a_new_version_must_be_higher(login, db, version):
    coder, user = login()
    store_bot(db, user["_id"], version="1.0.0")

    response = post_upload(coder, version=version)

    assert response.status_code == 400
    assert (response.json["code"], response.json["field"]) == ("invalid_parameter", "version")


def test_the_name_of_another_account_is_taken(login, db):
    coder, _ = login()
    other, _ = login("other")
    assert post_upload(other).status_code == 201

    response = post_upload(coder, name="SHARP", version="2.0.0")

    assert response.status_code == 409
    assert response.json["code"] == "name_taken"


def test_the_name_of_a_reference_bot_is_taken(login, reference_bots):
    coder, _ = login()

    response = post_upload(coder, name="random", version="2.0.0")

    assert response.status_code == 409
    assert response.json["code"] == "name_taken"


@pytest.mark.parametrize(
    ("files", "entry", "path"),
    [
        ({"bot.py": b"", "../escape.py": b""}, "bot.py", "../escape.py"),
        ({"bot.py": b"", "notes.txt": b""}, "bot.py", "notes.txt"),
        ({"helper.py": b""}, "bot.py", "bot.py"),
        ({"bot.py": b"", "Bot.py": b""}, "bot.py", "Bot.py"),
    ],
)
def test_files_against_the_rules_name_the_culprit(login, db, files, entry, path):
    coder, _ = login()

    response = post_upload(coder, files, entry=entry)

    assert response.status_code == 400
    assert (response.json["code"], response.json["path"]) == ("invalid_upload", path)
    assert db[BOTS].count_documents({"name": "Sharp"}) == 0


def test_too_much_data_is_against_the_rules(login):
    coder, _ = login()

    response = post_upload(coder, {"bot.py": b"", "data/big.bin": bytes(1024 * 1024 + 1)})

    assert response.status_code == 400
    assert response.json["code"] == "invalid_upload"
    assert "path" not in response.json


@pytest.mark.parametrize(
    ("fields", "field"),
    [
        ({"name": "ab"}, "name"),
        ({"name": "-dash"}, "name"),
        ({"version": "1.0"}, "version"),
        ({"version": "01.0.0"}, "version"),
        ({"language": "cpp"}, "language"),
        ({"comment": "hi"}, "comment"),
    ],
)
def test_invalid_fields(login, fields, field):
    coder, _ = login()

    response = post_upload(coder, **fields)

    assert response.status_code == 400
    assert (response.json["code"], response.json["field"]) == ("invalid_parameter", field)


def test_one_path_for_each_file(login):
    coder, _ = login()
    data = upload_form()
    data["paths"] = data["paths"][:2]

    response = coder.post(
        "/api/v1/bots", data=data, content_type="multipart/form-data", headers=CSRF
    )

    assert response.status_code == 400
    assert response.json["field"] == "paths"


def test_the_body_must_be_multipart(login):
    coder, _ = login()

    response = coder.post("/api/v1/bots", json={"name": "Sharp"}, headers=CSRF)

    assert response.status_code == 400
    assert response.json["field"] == "body"


def test_a_request_over_the_limit_is_too_large(login):
    coder, _ = login()

    response = post_upload(coder, {"bot.py": bytes(3 * 1024 * 1024)})

    assert response.status_code == 413
    assert response.json["code"] == "too_large"


def test_uploads_need_an_account(client):
    response = post_upload(client)

    assert response.status_code == 401


def test_uploads_are_limited_per_day(login, monkeypatch, clock):
    monkeypatch.setattr(rate_limit, "UPLOAD_LIMIT", 2)
    coder, _ = login()
    assert post_upload(coder, version="1.0.0").status_code == 201
    # A mistake does not count.
    assert post_upload(coder, version="1.0.0").status_code == 400
    assert post_upload(coder, version="1.0.1").status_code == 201

    response = post_upload(coder, version="1.0.2")

    assert response.status_code == 429
    assert response.json["code"] == "too_many_attempts"
    clock.advance(timedelta(days=1))
    assert post_upload(coder, version="1.0.2").status_code == 201


def test_a_lost_race_leaves_no_files(login, db, monkeypatch):
    coder, _ = login()
    monkeypatch.setattr(bots, "insert", lambda db, bot: False)

    response = post_upload(coder)

    assert response.status_code == 409
    assert response.json["code"] == "upload_conflict"
    assert db[f"{BOT_FILES}.files"].count_documents({}) == 0
    assert db[JOBS].count_documents({}) == 0
