from datetime import timedelta

from bson import ObjectId
from conftest import T0

from sbm_store import audit
from sbm_store.migrate import migrate

DAY = timedelta(days=1)


def record(db, action, *, actor="admin", target=None, at=T0):
    audit.record(db, actor_id=None, actor=actor, action=action, target=target, now=at)


def test_entries_come_newest_first_with_a_total(db):
    migrate(db)
    for hours in range(3):
        record(db, f"a{hours}", at=T0 + timedelta(hours=hours))

    items, total = audit.page(db, {}, limit=2, offset=0)

    assert [entry["action"] for entry in items] == ["a2", "a1"]
    assert total == 3
    assert [e["action"] for e in audit.page(db, {}, limit=2, offset=2)[0]] == ["a0"]


def test_filters_combine(db):
    migrate(db)
    bot_id = ObjectId()
    record(db, "bot.update", target=bot_id)
    record(db, "bot.update", actor="other", target=bot_id, at=T0 + DAY)
    record(db, "queue.pause", at=T0 + 2 * DAY)

    def actions(**conditions):
        items, _ = audit.page(db, audit.entry_filter(**conditions), limit=10, offset=0)
        return [(entry["actor"], entry["action"]) for entry in items]

    assert actions(action="bot.update", actor="admin") == [("admin", "bot.update")]
    assert actions(target=bot_id) == [("other", "bot.update"), ("admin", "bot.update")]
    assert actions(since=T0 + DAY, before=T0 + 2 * DAY) == [("other", "bot.update")]


def test_known_actions_and_actors(db):
    migrate(db)
    record(db, "queue.pause")
    record(db, "bot.update", actor="carol")
    record(db, "bot.update")

    assert audit.actions(db) == ["bot.update", "queue.pause"]
    assert audit.actors(db) == ["admin", "carol"]
