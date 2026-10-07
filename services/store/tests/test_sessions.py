from datetime import timedelta

from bson import ObjectId
from conftest import T0

from sbm_store import sessions
from sbm_store.tokens import token_hash

DAY = timedelta(days=1)


def test_a_session_is_found_by_its_token_until_it_expires(db):
    user_id = ObjectId()
    token = sessions.create(db, user_id, now=T0, expires_at=T0 + DAY)

    assert sessions.find(db, token, T0)["user_id"] == user_id
    assert sessions.find(db, token, T0 + DAY) is None
    assert sessions.find(db, "unknown", T0) is None


def test_only_the_hash_is_stored(db):
    token = sessions.create(db, ObjectId(), now=T0, expires_at=T0 + DAY)

    assert sessions.find(db, token, T0)["_id"] == token_hash(token)


def test_extend(db):
    token = sessions.create(db, ObjectId(), now=T0, expires_at=T0 + DAY)

    sessions.extend(db, token_hash(token), T0 + 2 * DAY)

    assert sessions.find(db, token, T0 + DAY) is not None


def test_delete_one_or_all_but_one(db):
    user_id = ObjectId()
    first, second, third = (
        sessions.create(db, user_id, now=T0, expires_at=T0 + DAY) for _ in range(3)
    )
    other = sessions.create(db, ObjectId(), now=T0, expires_at=T0 + DAY)

    sessions.delete(db, first)
    assert sessions.find(db, first, T0) is None

    sessions.delete_for_user(db, user_id, keep=token_hash(second))
    assert sessions.find(db, second, T0) is not None
    assert sessions.find(db, third, T0) is None
    assert sessions.find(db, other, T0) is not None

    sessions.delete_for_user(db, user_id)
    assert sessions.find(db, second, T0) is None
