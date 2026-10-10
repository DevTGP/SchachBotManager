"""GET /admin/settings and the four groups set by admins (E154)."""

import pytest
from sbm_store import account_settings, coder_settings, rating_recount
from sbm_store.account_settings import AccountSettings
from sbm_store.names import AUDIT_LOG

from accounts import CSRF, add_user

CODERS = {
    "games_per_day": 30,
    "uploads_per_day": 10,
    "games_per_request": 4,
    "max_initial_ms": 600_000,
    "max_increment_ms": 0,
    "priority": 40,
}
ACCOUNTS = {"invite_days": 3, "invite_max_days": 10, "login_failures": 3}
RATING = {"start": 1500, "base": 40, "step": 25, "max_win": 80, "min_win": 2, "max_draw": 40}
ESTIMATE = {"recent_games": 10, "moves_per_game": 100}


def put(admin, group: str, body: dict):
    return admin.put(f"/api/v1/admin/settings/{group}", json=body, headers=CSRF)


def test_the_defaults(admin):
    response = admin.get("/api/v1/admin/settings")

    assert response.status_code == 200
    assert response.json == {
        "coders": {
            "games_per_day": 20,
            "uploads_per_day": 20,
            "games_per_request": 10,
            "max_initial_ms": 300_000,
            "max_increment_ms": 5000,
            "priority": 50,
        },
        "accounts": {"invite_days": 7, "invite_max_days": 30, "login_failures": 5},
        "rating": {
            "start": 2500,
            "base": 50,
            "step": 20,
            "max_win": 100,
            "min_win": 1,
            "max_draw": 50,
        },
        "estimate": {"recent_games": 20, "moves_per_game": 80},
        "rating_recount_pending": False,
    }


@pytest.mark.parametrize(
    ("group", "body"),
    [("coders", CODERS), ("accounts", ACCOUNTS), ("rating", RATING), ("estimate", ESTIMATE)],
)
def test_each_group_is_saved_and_logged(admin, db, group, body):
    response = put(admin, group, body)

    assert response.status_code == 200
    assert response.json[group] == body
    assert admin.get("/api/v1/admin/settings").json[group] == body
    entry = db[AUDIT_LOG].find_one({"action": f"settings.{group}"})
    assert entry["details"] == body


@pytest.mark.parametrize(
    ("group", "body", "field"),
    [
        ("coders", CODERS | {"priority": 100}, "priority"),
        ("coders", CODERS | {"games_per_day": 0}, "games_per_day"),
        ("accounts", ACCOUNTS | {"invite_days": 11}, "invite_days"),
        ("rating", RATING | {"min_win": 41}, "min_win"),
        ("rating", RATING | {"max_win": 39}, "max_win"),
        ("estimate", ESTIMATE | {"recent_games": 201}, "recent_games"),
        ("estimate", {"recent_games": 10}, "moves_per_game"),
    ],
)
def test_invalid_settings_change_nothing(admin, db, group, body, field):
    response = put(admin, group, body)

    assert (response.status_code, response.json["field"]) == (400, field)
    assert db[AUDIT_LOG].count_documents({}) == 0
    assert not rating_recount.is_requested(db)


def test_a_changed_rating_rule_asks_for_a_recount(admin, db):
    assert put(admin, "rating", RATING).json["rating_recount_pending"] is True
    rating_recount.run_if_requested(db)

    # The same numbers again need no recount.
    assert put(admin, "rating", RATING).json["rating_recount_pending"] is False


def test_other_groups_do_not_ask_for_a_recount(admin):
    assert put(admin, "estimate", ESTIMATE).json["rating_recount_pending"] is False


def test_bots_without_counted_matches_stand_at_the_new_start(admin, client, reference_bots):
    put(admin, "rating", RATING)

    bot = client.get(f"/api/v1/bots/{reference_bots[0]['_id']}").json
    assert bot["rating"] == {"value": 1500, "games": 0}


def test_the_invite_validity_comes_from_the_settings(admin, db):
    account_settings.save(db, AccountSettings(invite_days=2, invite_max_days=3))
    create = "/api/v1/admin/invites"

    invite = admin.post(create, json={"role": "coder"}, headers=CSRF).json["invite"]
    too_long = admin.post(create, json={"role": "coder", "valid_days": 4}, headers=CSRF)

    assert invite["expires_at"] == "2026-05-03T12:00:00.000Z"
    assert (too_long.status_code, too_long.json["field"]) == (400, "valid_days")


def test_the_login_lock_comes_from_the_settings(client, db):
    account_settings.save(db, AccountSettings(login_failures=2))
    add_user(db, "alice")
    login = "/api/v1/session"
    wrong = {"username": "alice", "password": "wrong password"}
    for _ in range(2):
        assert client.post(login, json=wrong, headers=CSRF).status_code == 401

    assert client.post(login, json=wrong, headers=CSRF).status_code == 429


def test_coders_see_their_limits_without_the_priority(login, db):
    coder_settings.save(db, coder_settings.CoderSettings(games_per_day=7))
    client, _ = login()

    response = client.get("/api/v1/account/limits")

    assert response.status_code == 200
    assert response.json == {
        "games_per_day": 7,
        "uploads_per_day": 20,
        "games_per_request": 10,
        "max_initial_ms": 300_000,
        "max_increment_ms": 5000,
    }


def test_players_and_guests_have_no_limits(login, client):
    player, _ = login("anna", "player")

    assert player.get("/api/v1/account/limits").status_code == 403
    assert client.get("/api/v1/account/limits").status_code == 401
