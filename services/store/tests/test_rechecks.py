from datetime import timedelta

import pytest
from bson import ObjectId
from conftest import T0

from sbm_store import bot_deletion, bots, jobs, rechecks, verification_reports
from sbm_store.migrate import migrate
from sbm_store.names import JOBS


def bot(db, status=bots.VERIFIED, language="python") -> ObjectId:
    bot_id = ObjectId()
    document = bots.new_uploaded_bot(
        bot_id=bot_id,
        name=f"Bot{bot_id}",
        version="1.0",
        language=language,
        entry="bot.py",
        files=[],
        source_hash="",
        owner_id=ObjectId(),
        previous=None,
        now=T0,
    )
    assert bots.insert(db, document | {"status": status})
    return bot_id


def report(bot_id, kind, finished_at) -> dict:
    return verification_reports.new_report(
        bot_id=bot_id,
        job_id=ObjectId(),
        started_at=finished_at,
        finished_at=finished_at,
        passed=True,
        ruleset=None,
        runtime={},
        stages=[],
        kind=kind,
    )


def test_a_recheck_is_a_verification_job_marked_as_such(db):
    bot_id = bot(db)

    assert rechecks.request(db, bot_id, T0)

    job = db[JOBS].find_one({"payload.bot_id": bot_id})
    assert (job["type"], job["priority"], jobs.is_recheck(job)) == (
        jobs.VERIFICATION,
        jobs.VERIFICATION_PRIORITY,
        True,
    )
    assert not jobs.is_recheck(jobs.new_verification_job(bot_id, now=T0))


def test_a_bot_gets_no_second_recheck_while_one_is_pending(db):
    bot_id = bot(db)
    assert rechecks.request(db, bot_id, T0)

    assert not rechecks.request(db, bot_id, T0)

    jobs.claim(db, jobs.VERIFICATION, "w", now=T0, lease=timedelta(minutes=1))
    assert not rechecks.request(db, bot_id, T0)
    db[JOBS].update_many({}, {"$set": {"status": jobs.DONE}})
    assert rechecks.request(db, bot_id, T0)


def test_a_language_rechecks_its_verified_and_rejected_uploads(db):
    migrate(db)
    verified = bot(db)
    rejected = bot(db, bots.REJECTED)
    bot(db, bots.DISABLED)
    bot(db, bots.TESTING)
    bot(db, language="cpp")
    pending = bot(db)
    rechecks.request(db, pending, T0)

    assert rechecks.request_language(db, "python", T0) == 2

    queued = {job["payload"]["bot_id"] for job in db[JOBS].find({"type": jobs.VERIFICATION})}
    assert queued == {verified, rejected, pending}


def test_rechecks_of_lists_only_rechecks_newest_first(db):
    bot_id = bot(db)
    older = report(bot_id, verification_reports.RECHECK, T0)
    newer = report(bot_id, verification_reports.RECHECK, T0 + timedelta(hours=1))
    for item in (older, newer, report(bot_id, verification_reports.UPLOAD, T0)):
        verification_reports.insert(db, item)
    verification_reports.insert(db, report(ObjectId(), verification_reports.RECHECK, T0))

    listed = verification_reports.rechecks_of(db, bot_id)

    assert [item["_id"] for item in listed] == [newer["_id"], older["_id"]]


def test_override_verifies_only_a_rejected_bot_and_keeps_the_rejection(db):
    rejected = bot(db, bots.REJECTED)
    db["bots"].update_one({"_id": rejected}, {"$set": {"rejection": {"stage": "analysis"}}})

    overridden = bots.override(db, rejected, T0)

    assert overridden["status"] == bots.VERIFIED
    assert overridden["verified_at"] == overridden["overridden_at"]
    assert overridden["rejection"] == {"stage": "analysis"}
    assert bots.override(db, rejected, T0) is None
    assert bots.override(db, ObjectId(), T0) is None


def test_a_bot_in_a_running_recheck_cannot_be_deleted(db):
    bot_id = bot(db)
    rechecks.request(db, bot_id, T0)
    jobs.claim(db, jobs.VERIFICATION, "w", now=T0, lease=timedelta(minutes=1))

    with pytest.raises(bot_deletion.NotDeletable) as raised:
        bot_deletion.delete_bot(db, bot_id, T0)

    assert raised.value.reason == bot_deletion.VERIFYING
