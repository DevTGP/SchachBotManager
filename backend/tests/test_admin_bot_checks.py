from datetime import timedelta

from bson import ObjectId
from sbm_store import bots, jobs, verification_reports
from sbm_store.names import AUDIT_LOG, JOBS

from accounts import CSRF
from bot_uploads import store_bot, verify
from stored_games import NOW


def recheck(client, bot: dict):
    return client.post(f"/api/v1/admin/bots/{bot['_id']}/recheck", headers=CSRF)


def recheck_report(db, bot: dict, *, passed: bool) -> None:
    """A finished recheck, as the runner writes it."""
    report = verification_reports.new_report(
        bot_id=bot["_id"],
        job_id=ObjectId(),
        started_at=NOW,
        finished_at=NOW + timedelta(hours=1),
        passed=passed,
        ruleset="python-2",
        runtime={},
        stages=[],
        kind=verification_reports.RECHECK,
    )
    verification_reports.insert(db, report)


def test_a_recheck_queues_a_job_and_keeps_the_bot(admin, db):
    bot = verify(db, store_bot(db, ObjectId()))

    response = recheck(admin, bot)

    assert response.status_code == 202
    details = response.json["details"]
    assert (response.json["status"], details["recheck_pending"]) == (bots.VERIFIED, True)
    assert details["report"]["result"] == "passed"
    job = db[JOBS].find_one({"payload.bot_id": bot["_id"]})
    assert (job["type"], jobs.is_recheck(job)) == (jobs.VERIFICATION, True)
    entry = db[AUDIT_LOG].find_one({"action": "bot.recheck"})
    assert (entry["target"], entry["details"]) == (bot["_id"], {"status": bots.VERIFIED})


def test_a_bot_gets_one_recheck_at_a_time(admin, db):
    bot = verify(db, store_bot(db, ObjectId()))
    recheck(admin, bot)

    response = recheck(admin, bot)

    assert response.status_code == 409
    assert response.json["code"] == "bot_verifying"
    assert db[JOBS].count_documents({"payload.bot_id": bot["_id"]}) == 1


def test_a_bot_in_its_upload_verification_is_not_rechecked(admin, db):
    response = recheck(admin, store_bot(db, ObjectId()))

    assert response.status_code == 409
    assert response.json["code"] == "bot_verifying"


def test_reference_bots_are_not_rechecked(admin, db, reference_bots):
    response = recheck(admin, reference_bots[0])

    assert response.status_code == 409
    assert response.json["code"] == "builtin_bot"


def test_unknown_bot(admin):
    response = admin.post(f"/api/v1/admin/bots/{ObjectId()}/recheck", headers=CSRF)

    assert response.status_code == 404


def test_rechecks_show_to_the_owner_newest_first_but_not_to_others(app, db, login):
    owner, user = login()
    bot = verify(db, store_bot(db, user["_id"]), passed=False)
    recheck_report(db, bot, passed=True)
    url = f"/api/v1/bots/{bot['_id']}"

    details = owner.get(url).json["details"]

    assert [item["result"] for item in details["rechecks"]] == ["passed"]
    assert details["report"]["result"] == "failed"
    assert details["recheck_pending"] is False
    assert app.test_client().get(url).status_code == 404


def test_a_language_recheck_queues_the_verified_and_rejected_uploads(admin, db):
    verify(db, store_bot(db, ObjectId(), name="One"))
    verify(db, store_bot(db, ObjectId(), name="Two"), passed=False)
    store_bot(db, ObjectId(), name="Three")

    response = admin.post("/api/v1/admin/bots/recheck", json={"language": "python"}, headers=CSRF)

    assert response.status_code == 202
    assert response.json == {"queued": 2}
    entry = db[AUDIT_LOG].find_one({"action": "bot.recheck_language"})
    assert entry["details"] == {"language": "python", "queued": 2}


def test_a_language_recheck_needs_a_known_language(admin):
    response = admin.post("/api/v1/admin/bots/recheck", json={"language": "rust"}, headers=CSRF)

    assert response.status_code == 400
    assert response.json["field"] == "language"


def test_override_verifies_a_rejected_bot_and_keeps_the_rejection(admin, db):
    bot = verify(db, store_bot(db, ObjectId()), passed=False)

    response = admin.post(f"/api/v1/admin/bots/{bot['_id']}/override", headers=CSRF)

    assert response.status_code == 200
    assert response.json["status"] == bots.VERIFIED
    details = response.json["details"]
    assert details["overridden_at"] is not None
    assert details["rejection"] == {"stage": "analysis", "reason": "1 finding"}
    entry = db[AUDIT_LOG].find_one({"action": "bot.override"})
    assert (entry["target"], entry["details"]) == (bot["_id"], {"stage": "analysis"})


def test_only_a_rejected_bot_can_be_overridden(admin, db):
    bot = verify(db, store_bot(db, ObjectId()))

    response = admin.post(f"/api/v1/admin/bots/{bot['_id']}/override", headers=CSRF)

    assert response.status_code == 409
    assert response.json["code"] == "bot_state"
    assert db[AUDIT_LOG].count_documents({"action": "bot.override"}) == 0
