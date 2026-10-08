"""PATCH /bots/{bot_id}: description and retiring by the owner (E95, E96)."""

import pytest
from bson import ObjectId
from sbm_store import bots

from accounts import CSRF
from bot_uploads import store_bot, verify


def patch(client, bot, body):
    return client.patch(f"/api/v1/bots/{bot['_id']}", json=body, headers=CSRF)


def test_the_owner_retires_and_reactivates(login, db):
    coder, user = login()
    bot = verify(db, store_bot(db, user["_id"]))

    response = patch(coder, bot, {"status": "retired", "description": "Line one\r\nline two"})

    assert response.status_code == 200
    assert response.json["status"] == bots.RETIRED
    assert response.json["description"] == "Line one\nline two"
    assert response.json["details"]["owner"] == "coder"
    assert patch(coder, bot, {"status": "verified"}).json["status"] == bots.VERIFIED


def test_the_description_changes_in_any_status(login, db):
    coder, user = login()
    bot = store_bot(db, user["_id"])

    response = patch(coder, bot, {"description": "Still in verification."})

    assert response.status_code == 200
    assert (response.json["status"], response.json["description"]) == (
        bots.UPLOADED,
        "Still in verification.",
    )


def test_an_admin_block_stays(login, db):
    coder, user = login()
    bot = verify(db, store_bot(db, user["_id"]))
    bots.set_enabled(db, bot["_id"], False)

    response = patch(coder, bot, {"status": "verified", "description": "Lifted?"})

    assert response.status_code == 400
    assert response.json["field"] == "status"
    stored = bots.get(db, bot["_id"])
    assert (stored["status"], stored["description"]) == (bots.DISABLED, "")


def test_a_bot_in_verification_cannot_retire(login, db):
    coder, user = login()
    bot = store_bot(db, user["_id"])
    assert patch(coder, bot, {"status": "retired"}).status_code == 400


@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({}, "body"),
        ({"status": "disabled"}, "status"),
        ({"description": 5}, "description"),
        ({"description": "x" * 501}, "description"),
        ({"description": "tab\there"}, "description"),
        ({"name": "Other"}, "name"),
    ],
)
def test_invalid_changes(login, db, body, field):
    coder, user = login()
    bot = verify(db, store_bot(db, user["_id"]))

    response = patch(coder, bot, body)

    assert response.status_code == 400
    assert response.json["field"] == field


def test_only_the_owner_changes_a_bot(client, login, admin, db, reference_bots):
    other, _ = login("other")
    _, user = login()
    public = verify(db, store_bot(db, user["_id"]))
    hidden = store_bot(db, user["_id"], name="Hidden")
    body = {"description": "Mine now."}

    assert patch(client, public, body).status_code == 401
    assert patch(other, public, body).status_code == 403
    assert patch(admin, public, body).status_code == 403
    assert patch(other, hidden, body).status_code == 404
    assert patch(admin, reference_bots[0], body).status_code == 403
    assert patch(other, {"_id": ObjectId()}, body).status_code == 404
    assert bots.get(db, public["_id"])["description"] == ""
