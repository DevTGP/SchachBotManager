from datetime import timedelta

from bson import ObjectId
from conftest import T0

from sbm_store import invites, users
from sbm_store.migrate import migrate

WEEK = timedelta(days=7)


def create(db, *, now=T0, valid=WEEK):
    return invites.create(
        db, users.CODER, created_by=None, created_by_name=None, now=now, expires_at=now + valid
    )


def test_an_invite_can_be_claimed_once(db):
    migrate(db)
    invite, token = create(db)

    claimed = invites.claim(db, token, T0)

    assert claimed["_id"] == invite["_id"]
    assert invites.claim(db, token, T0) is None


def test_expired_or_unknown_tokens_claim_nothing(db):
    migrate(db)
    _, token = create(db)

    assert invites.claim(db, token, T0 + WEEK) is None
    assert invites.claim(db, "unknown", T0) is None


def test_a_released_invite_can_be_claimed_again(db):
    migrate(db)
    invite, token = create(db)
    invites.claim(db, token, T0)

    invites.release(db, invite["_id"])

    assert invites.claim(db, token, T0) is not None


def test_open_invites_are_unused_and_valid_newest_first(db):
    migrate(db)
    older, _ = create(db)
    newer, _ = create(db, now=T0 + timedelta(hours=1))
    _, used = create(db)
    create(db, valid=timedelta(minutes=1))
    invites.claim(db, used, T0)

    found = invites.open_invites(db, T0 + timedelta(hours=2))

    assert [invite["_id"] for invite in found] == [newer["_id"], older["_id"]]


def test_revoke_only_unused_invites(db):
    migrate(db)
    invite, _ = create(db)
    used, token = create(db)
    invites.claim(db, token, T0)

    assert invites.revoke(db, invite["_id"])
    assert not invites.revoke(db, invite["_id"])
    assert not invites.revoke(db, used["_id"])
    assert not invites.revoke(db, ObjectId())


def test_mark_used_by(db):
    migrate(db)
    invite, token = create(db)
    user_id = ObjectId()
    invites.claim(db, token, T0)

    invites.mark_used_by(db, invite["_id"], user_id)

    assert db.invites.find_one({"_id": invite["_id"]})["used_by"] == user_id
