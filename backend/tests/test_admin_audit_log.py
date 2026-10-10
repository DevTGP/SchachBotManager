from datetime import timedelta

from bson import ObjectId
from sbm_store import audit

from stored_games import NOW


def record(db, action, *, actor="admin", target=None, details=None, at=NOW):
    audit.record(
        db, actor_id=None, actor=actor, action=action, target=target, details=details, now=at
    )


def entries(admin, query=""):
    response = admin.get(f"/api/v1/admin/audit{query}")
    assert response.status_code == 200
    return response.json


def test_entries_newest_first_with_filter_choices(admin, db):
    bot_id = ObjectId()
    record(db, "bot.update", target=bot_id, details={"status": "disabled"})
    record(db, "invite.create", actor=audit.CLI, at=NOW + timedelta(hours=1))

    page = entries(admin)

    assert [item["action"] for item in page["items"]] == ["invite.create", "bot.update"]
    assert page["total"] == 2
    assert page["actions"] == ["bot.update", "invite.create"]
    assert page["actors"] == ["admin", "cli"]
    assert page["items"][1]["target"] == str(bot_id)
    assert page["items"][1]["details"] == {"status": "disabled"}
    assert page["items"][1]["at"] == "2026-05-01T12:00:00.000Z"


def test_filters_by_actor_action_target_and_day(admin, db):
    bot_id = ObjectId()
    record(db, "bot.update", target=bot_id)
    record(db, "bot.update", actor="carol", target=bot_id, at=NOW + timedelta(days=1))
    record(db, "queue.pause", at=NOW + timedelta(days=2))

    def actions(query):
        return [(item["actor"], item["action"]) for item in entries(admin, query)["items"]]

    assert actions("?actor=carol") == [("carol", "bot.update")]
    assert actions("?action=queue.pause") == [("admin", "queue.pause")]
    assert actions(f"?target={bot_id}&actor=admin") == [("admin", "bot.update")]
    assert actions("?since=2026-05-02&until=2026-05-02") == [("carol", "bot.update")]
    assert entries(admin, "?limit=1&offset=1")["total"] == 3


def test_details_with_ids_and_times_become_strings(admin, db):
    match_id = ObjectId()
    record(db, "match.enqueue", details={"ids": [match_id], "at": NOW})

    details = entries(admin)["items"][0]["details"]

    assert details == {"ids": [str(match_id)], "at": "2026-05-01T12:00:00.000Z"}


def test_invalid_filters(admin):
    for query, field in (("?since=2026-5-1", "since"), ("?until=2026-02-30", "until")):
        response = admin.get(f"/api/v1/admin/audit{query}")
        assert response.status_code == 400
        assert response.json["field"] == field


def test_open_ended_periods(admin, db):
    record(db, "queue.pause")

    assert entries(admin, "?until=9999-12-31")["total"] == 1
    assert entries(admin, "?since=0001-01-01")["total"] == 1
