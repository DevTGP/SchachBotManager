"""Accounts in leagues and tournaments: registering, leaving and their views (E182, E186)."""

from sbm_store import registrations
from sbm_store.names import AUDIT_LOG, REGISTRATIONS
from stored_tournaments import start_edition, store_tournament

from accounts import CSRF, add_user
from stored_leagues import start_season, store_league


def register(client, path, **fields):
    return client.post(f"/api/v1/{path}/registrations", json=fields, headers=CSRF)


def deregister(client, path, participant_id):
    return client.delete(f"/api/v1/{path}/registrations/{participant_id}", headers=CSRF)


def human(user):
    return {
        "kind": "human",
        "bot_id": None,
        "user_id": str(user["_id"]),
        "name": user["username"],
        "version": None,
    }


def test_a_player_registers_and_leaves_a_league(login, db):
    client, user = login("pat", "player")
    league = store_league(db)
    path = f"leagues/{league['_id']}"

    first = register(client, path, user_id=str(user["_id"]))
    again = register(client, path, user_id=str(user["_id"]))
    detail = client.get(f"/api/v1/{path}").json

    assert first.status_code == 201
    assert first.json["bot"] == human(user)
    assert (again.status_code, again.json["code"]) == (409, "already_registered")
    assert again.json["field"] == "user_id"
    assert [entry["bot"] for entry in detail["registrations"]] == [human(user)]
    assert db[AUDIT_LOG].count_documents({}) == 0
    assert deregister(client, path, user["_id"]).status_code == 204
    assert deregister(client, path, user["_id"]).status_code == 404
    assert registrations.get_active(db, league["_id"], user["_id"]) is None


def test_a_registration_names_exactly_one_participant(login, db, reference_bots):
    client, user = login()
    path = f"leagues/{store_league(db)['_id']}"

    both = register(client, path, user_id=str(user["_id"]), bot_id=str(reference_bots[0]["_id"]))
    neither = client.post(f"/api/v1/{path}/registrations", json={}, headers=CSRF)

    assert (both.status_code, both.json["field"]) == (400, "body")
    assert (neither.status_code, neither.json["field"]) == (400, "body")


def test_only_admins_register_other_accounts(login, admin, db):
    client, _ = login()
    other, _ = add_user(db, "other", "player")
    inactive, _ = add_user(db, "gone", "player", active=False)
    path = f"leagues/{store_league(db)['_id']}"

    assert register(client, path, user_id=str(other["_id"])).status_code == 403
    response = register(admin, path, user_id=str(other["_id"]))
    refused = register(admin, path, user_id=str(inactive["_id"]))

    assert response.status_code == 201
    assert (refused.status_code, refused.json["code"]) == (409, "user_state")
    assert deregister(client, path, other["_id"]).status_code == 403
    assert deregister(admin, path, other["_id"]).status_code == 204
    actions = [entry["action"] for entry in db[AUDIT_LOG].find().sort("_id")]
    assert actions == ["league.register_account", "league.deregister_account"]
    audit = admin.get("/api/v1/admin/audit").json["items"]
    assert {(item["target_kind"], item["target_label"]) for item in audit} == {("user", "other")}


def test_accounts_in_tournaments(login, admin, db):
    client, user = login("pat", "player")
    path = f"tournaments/{store_tournament(db)['_id']}"

    response = register(client, path, user_id=str(user["_id"]))
    listed = client.get(f"/api/v1/{path}").json

    assert response.status_code == 201
    assert response.json["bot"] == human(user)
    assert [entry["bot"] for entry in listed["registrations"]] == [human(user)]
    assert deregister(admin, path, user["_id"]).status_code == 204
    assert db[AUDIT_LOG].find_one()["action"] == "tournament.deregister_account"


def test_deactivating_an_account_ends_its_registrations(admin, db):
    user, _ = add_user(db, "pat", "player")
    register(admin, f"leagues/{store_league(db)['_id']}", user_id=str(user["_id"]))

    path = f"/api/v1/admin/users/{user['_id']}"
    response = admin.patch(path, json={"active": False}, headers=CSRF)

    assert response.status_code == 200
    left = db[REGISTRATIONS].find_one({"user_id": user["_id"]})
    assert (left["status"], left["left_reason"]) == (registrations.LEFT, registrations.DEACTIVATED)


def test_seasons_and_editions_show_accounts(client, db, reference_bots):
    user, _ = add_user(db, "pat", "player")
    season = start_season(db, store_league(db), [reference_bots[0], user])
    edition = start_edition(db, store_tournament(db), [reference_bots[1], user])

    (tier,) = client.get(f"/api/v1/seasons/{season['_id']}").json["tiers"]
    shown = client.get(f"/api/v1/editions/{edition['_id']}").json

    assert {row["bot"]["kind"] for row in tier["table"]} == {"bot", "human"}
    assert human(user) in [entry["bot"] for entry in shown["participants"]]
