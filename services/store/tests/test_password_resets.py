from datetime import timedelta

from bson import ObjectId
from conftest import T0

from sbm_store import password_resets
from sbm_store.migrate import migrate

DAY = timedelta(days=1)


def create(db, user_id):
    return password_resets.create(db, user_id, created_by=None, now=T0, expires_at=T0 + DAY)


def test_a_link_works_once(db):
    migrate(db)
    user_id = ObjectId()
    _, token = create(db, user_id)

    assert password_resets.redeem(db, token, T0)["user_id"] == user_id
    assert password_resets.redeem(db, token, T0) is None


def test_an_expired_link_does_not_work(db):
    migrate(db)
    _, token = create(db, ObjectId())

    assert password_resets.redeem(db, token, T0 + DAY) is None


def test_a_new_link_replaces_the_old_one(db):
    migrate(db)
    user_id = ObjectId()
    _, old = create(db, user_id)
    _, new = create(db, user_id)

    assert password_resets.redeem(db, old, T0) is None
    assert password_resets.redeem(db, new, T0) is not None
