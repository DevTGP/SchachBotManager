"""POST and DELETE /leagues/{league_id}/registrations, and leaving through the bot (E136)."""

from sbm_store import bots, leagues, matches, registrations, seasons
from sbm_store.names import AUDIT_LOG, MATCHES, REGISTRATIONS

from accounts import CSRF
from bot_uploads import store_bot, verify
from stored_games import NOW
from stored_leagues import start_season, store_league


def register(client, league, bot):
    return client.post(
        f"/api/v1/leagues/{league['_id']}/registrations",
        json={"bot_id": str(bot["_id"])},
        headers=CSRF,
    )


def deregister(client, league, bot):
    return client.delete(
        f"/api/v1/leagues/{league['_id']}/registrations/{bot['_id']}", headers=CSRF
    )


def own_bot(db, user, name="Sharp"):
    return verify(db, store_bot(db, user["_id"], name=name))


def test_the_owner_registers_a_verified_bot_once(login, db):
    client, user = login()
    league = store_league(db)
    bot = own_bot(db, user)

    first = register(client, league, bot)
    again = register(client, league, bot)

    assert first.status_code == 201
    assert first.json["bot"] == {"bot_id": str(bot["_id"]), "name": "Sharp", "version": "1.0.0"}
    assert first.json["tier"] is None
    assert (again.status_code, again.json["code"]) == (409, "already_registered")
    listed = client.get(f"/api/v1/bots/{bot['_id']}/leagues").json["items"]
    assert [entry["league_name"] for entry in listed] == ["Liga"]
    assert db[AUDIT_LOG].count_documents({}) == 0


def test_only_verified_bots_in_leagues_in_use(login, db):
    client, user = login()
    league = store_league(db)
    waiting = store_bot(db, user["_id"])
    archived = store_league(db, "Alt")
    leagues.update(db, archived["_id"], {"archived": True}, now=NOW)

    assert register(client, league, waiting).json["code"] == "bot_state"
    verified = own_bot(db, user, "Other")
    assert register(client, archived, verified).json["code"] == "league_state"


def test_others_may_not_register_a_bot_but_admins_may(login, admin, db):
    owner_client, owner = login()
    other, _ = login("other")
    league = store_league(db)
    bot = own_bot(db, owner)

    assert register(other, league, bot).status_code == 403
    assert register(admin, league, bot).status_code == 201
    assert db[AUDIT_LOG].find_one({"action": "league.register"})["target"] == bot["_id"]
    assert deregister(owner_client, league, bot).status_code == 204


def test_leaving_a_running_season_forfeits_the_waiting_games(login, db, reference_bots):
    client, user = login()
    bot = own_bot(db, user)
    league = store_league(db)
    season = start_season(db, league, [*reference_bots, bot])

    response = deregister(client, league, bot)

    assert response.status_code == 204
    assert registrations.get_active(db, league["_id"], bot["_id"]) is None
    assert seasons.get(db, season["_id"])["withdrawn"] == [bot["_id"]]
    played = matches.match_filter(bot_id=bot["_id"], season_id=season["_id"])
    own = list(db[MATCHES].find(played))
    assert own
    assert {game["termination"] for game in own} == {matches.FORFEIT}
    assert deregister(client, league, bot).status_code == 404


def test_retiring_a_bot_ends_its_registrations(login, db):
    client, user = login()
    bot = own_bot(db, user)
    league = store_league(db)
    register(client, league, bot)

    response = client.patch(
        f"/api/v1/bots/{bot['_id']}", json={"status": bots.RETIRED}, headers=CSRF
    )

    assert response.status_code == 200
    assert registrations.get_active(db, league["_id"], bot["_id"]) is None


def test_disabling_a_bot_ends_its_registrations(login, admin, db):
    client, user = login()
    bot = own_bot(db, user)
    league = store_league(db)
    register(client, league, bot)

    response = admin.patch(
        f"/api/v1/admin/bots/{bot['_id']}", json={"status": bots.DISABLED}, headers=CSRF
    )

    assert response.status_code == 200
    left = db[REGISTRATIONS].find_one({"bot_id": bot["_id"]})
    assert (left["status"], left["left_reason"]) == (registrations.LEFT, registrations.DISABLED)
