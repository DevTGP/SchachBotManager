from bson import ObjectId
from sbm_store import bots
from sbm_store.names import AUDIT_LOG

from accounts import CSRF
from bot_uploads import store_bot, verify


def test_disable_and_enable_a_bot_and_record_it(admin, db):
    bot = verify(db, store_bot(db, ObjectId()))

    response = admin.patch(
        f"/api/v1/admin/bots/{bot['_id']}", json={"status": "disabled"}, headers=CSRF
    )

    assert response.status_code == 200
    assert response.json["status"] == bots.DISABLED
    assert response.json["details"]["report"]["result"] == "passed"
    entry = db[AUDIT_LOG].find_one({"action": "bot.update"})
    assert (entry["actor"], entry["target"], entry["details"]) == (
        "admin",
        bot["_id"],
        {"status": "disabled"},
    )
    response = admin.patch(
        f"/api/v1/admin/bots/{bot['_id']}", json={"status": "verified"}, headers=CSRF
    )
    assert response.json["status"] == bots.VERIFIED


def test_a_retired_bot_can_be_disabled_but_not_enabled(admin, db):
    bot = verify(db, store_bot(db, ObjectId()))
    bots.change_by_owner(db, bot["_id"], retired=True)
    url = f"/api/v1/admin/bots/{bot['_id']}"

    response = admin.patch(url, json={"status": "verified"}, headers=CSRF)

    assert response.status_code == 400
    assert response.json["message"] == "the bot cannot switch to verified"
    assert admin.patch(url, json={"status": "disabled"}, headers=CSRF).status_code == 200
    response = admin.patch(url, json={"status": "verified"}, headers=CSRF)
    assert response.json["status"] == bots.VERIFIED


def test_a_bot_in_verification_cannot_be_switched(admin, db):
    bot = store_bot(db, ObjectId())

    response = admin.patch(
        f"/api/v1/admin/bots/{bot['_id']}", json={"status": "verified"}, headers=CSRF
    )

    assert response.status_code == 400
    assert bots.get(db, bot["_id"])["status"] == bots.UPLOADED


def test_only_two_statuses(admin, db):
    bot = verify(db, store_bot(db, ObjectId()))

    response = admin.patch(
        f"/api/v1/admin/bots/{bot['_id']}", json={"status": "rejected"}, headers=CSRF
    )

    assert response.status_code == 400
    assert response.json["field"] == "status"


def test_unknown_bot(admin):
    response = admin.patch(
        f"/api/v1/admin/bots/{ObjectId()}", json={"status": "disabled"}, headers=CSRF
    )
    assert response.status_code == 404
