from dataclasses import replace

from bson import ObjectId
from sbm_store import bots, matches, rating_recount
from sbm_store.discipline import STANDARD_FEN
from sbm_store.enqueue import enqueue_match
from sbm_store.names import AUDIT_LOG
from sbm_store.ratings import count_pending

from accounts import CSRF
from bot_uploads import store_bot, verify
from stored_games import BLITZ, NOW, finish_by_resignation


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


def test_delete_a_bot_with_its_matches_and_record_it(admin, db, reference_bots):
    bot = verify(db, store_bot(db, ObjectId()))
    random, material = reference_bots
    played = enqueue_match(db, bot, random, BLITZ, start_fen=STANDARD_FEN, now=NOW)
    finish_by_resignation(db, played, NOW)
    other = enqueue_match(db, random, material, BLITZ, start_fen=STANDARD_FEN, now=NOW)

    response = admin.delete(f"/api/v1/admin/bots/{bot['_id']}", headers=CSRF)

    assert response.status_code == 204
    assert bots.get(db, bot["_id"]) is None
    assert matches.get(db, played) is None
    assert matches.get(db, other) is not None
    entry = db[AUDIT_LOG].find_one({"action": "bot.delete"})
    assert (entry["target"], entry["details"]) == (
        bot["_id"],
        {"name": "Sharp", "version": "1.0.0", "matches": 1},
    )
    assert admin.get(f"/api/v1/bots/{bot['_id']}").status_code == 404


def test_deleting_counted_matches_asks_the_runner_to_count_again(admin, db, reference_bots):
    bot = verify(db, store_bot(db, ObjectId()))
    rated = replace(BLITZ, discipline_id=ObjectId())
    played = enqueue_match(db, bot, reference_bots[0], rated, start_fen=STANDARD_FEN, now=NOW)
    finish_by_resignation(db, played, NOW)
    assert count_pending(db) == 1

    assert admin.delete(f"/api/v1/admin/bots/{bot['_id']}", headers=CSRF).status_code == 204

    assert rating_recount.is_requested(db)


def test_the_name_is_free_once_no_version_is_left(admin, db):
    owner = ObjectId()
    first = verify(db, store_bot(db, owner))
    second = verify(db, store_bot(db, owner, version="2.0.0"))

    admin.delete(f"/api/v1/admin/bots/{second['_id']}", headers=CSRF)
    assert bots.latest(db, "Sharp")["_id"] == first["_id"]
    admin.delete(f"/api/v1/admin/bots/{first['_id']}", headers=CSRF)
    assert bots.latest(db, "Sharp") is None


def test_some_bots_cannot_be_deleted(admin, db, reference_bots):
    verifying = store_bot(db, ObjectId())
    playing = verify(db, store_bot(db, ObjectId(), name="Busy"))
    match_id = enqueue_match(db, playing, reference_bots[0], BLITZ, start_fen=STANDARD_FEN, now=NOW)
    matches.start(db, match_id, NOW)

    for bot, code in [
        (reference_bots[0], "builtin_bot"),
        (verifying, "bot_verifying"),
        (playing, "bot_playing"),
    ]:
        response = admin.delete(f"/api/v1/admin/bots/{bot['_id']}", headers=CSRF)
        assert (response.status_code, response.json["code"]) == (409, code)
        assert bots.get(db, bot["_id"]) is not None


def test_delete_an_unknown_bot(admin):
    assert admin.delete(f"/api/v1/admin/bots/{ObjectId()}", headers=CSRF).status_code == 404
