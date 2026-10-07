from datetime import timedelta

from bson import ObjectId
from conftest import T0

from sbm_store import users
from sbm_store.migrate import migrate


def add(db, username, role=users.CODER):
    user = users.new_user(username, "hash", role, invited_by=None, now=T0)
    assert users.insert(db, user)
    return user


def test_usernames_are_unique_regardless_of_case(db):
    migrate(db)
    add(db, "Alice")

    assert not users.insert(db, users.new_user("alice", "h", users.CODER, invited_by=None, now=T0))
    assert users.username_taken(db, "ALICE")
    assert users.by_username(db, "aLiCe")["username"] == "Alice"


def test_listed_by_name_regardless_of_case(db):
    migrate(db)
    for name in ("carol", "Bob", "alice"):
        add(db, name)

    assert [user["username"] for user in users.all_by_name(db)] == ["alice", "Bob", "carol"]


def test_update_returns_the_changed_user(db):
    migrate(db)
    user = add(db, "alice")

    changed = users.update(db, user["_id"], {"role": users.ADMIN, "active": False})

    assert (changed["role"], changed["active"]) == (users.ADMIN, False)
    assert users.update(db, ObjectId(), {"active": True}) is None


def test_failed_logins_count_until_a_login_or_lock(db):
    migrate(db)
    user = add(db, "alice")

    assert [users.count_failed_login(db, user["_id"]) for _ in range(3)] == [1, 2, 3]
    users.lock(db, user["_id"], T0 + timedelta(minutes=15))
    assert users.get(db, user["_id"])["locked_until"] == T0 + timedelta(minutes=15)
    assert users.count_failed_login(db, user["_id"]) == 1

    users.record_login(db, user["_id"], T0)
    stored = users.get(db, user["_id"])
    assert stored["failed_logins"] == 0
    assert stored["locked_until"] is None
    assert stored["last_login_at"] == T0
