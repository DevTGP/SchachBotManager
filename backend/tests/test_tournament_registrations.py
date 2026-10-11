"""POST and DELETE /tournaments/{tournament_id}/registrations, and leaving through the bot
(E179)."""

from sbm_store import bots, editions, matches, registrations, tournaments
from sbm_store.names import AUDIT_LOG, MATCHES, REGISTRATIONS
from stored_tournaments import start_edition, store_tournament

from accounts import CSRF
from bot_uploads import store_bot, verify
from stored_games import NOW

TOURNAMENT = registrations.TOURNAMENT


def register(client, tournament, bot):
    return client.post(
        f"/api/v1/tournaments/{tournament['_id']}/registrations",
        json={"bot_id": str(bot["_id"])},
        headers=CSRF,
    )


def deregister(client, tournament, bot):
    return client.delete(
        f"/api/v1/tournaments/{tournament['_id']}/registrations/{bot['_id']}", headers=CSRF
    )


def own_bot(db, user, name="Sharp"):
    return verify(db, store_bot(db, user["_id"], name=name))


def active(db, tournament, bot):
    return registrations.get_active(db, tournament["_id"], bot["_id"], target_type=TOURNAMENT)


def test_the_owner_registers_a_verified_bot_once(login, db):
    client, user = login()
    tournament = store_tournament(db)
    bot = own_bot(db, user)

    first = register(client, tournament, bot)
    again = register(client, tournament, bot)

    assert first.status_code == 201
    assert first.json["bot"] == {"bot_id": str(bot["_id"]), "name": "Sharp", "version": "1.0.0"}
    assert (first.json["tournament_name"], first.json["playing"]) == ("Pokal", False)
    assert (again.status_code, again.json["code"]) == (409, "already_registered")
    assert db[AUDIT_LOG].count_documents({}) == 0


def test_only_verified_bots_in_tournaments_in_use(login, db):
    client, user = login()
    tournament = store_tournament(db)
    waiting = store_bot(db, user["_id"])
    archived = store_tournament(db, "Alt")
    tournaments.update(db, archived["_id"], {"archived": True}, now=NOW)

    assert register(client, tournament, waiting).json["code"] == "bot_state"
    verified = own_bot(db, user, "Other")
    assert register(client, archived, verified).json["code"] == "tournament_state"


def test_others_may_not_register_a_bot_but_admins_may(login, admin, db):
    owner_client, owner = login()
    other, _ = login("other")
    tournament = store_tournament(db)
    bot = own_bot(db, owner)

    assert register(other, tournament, bot).status_code == 403
    assert register(admin, tournament, bot).status_code == 201
    entry = db[AUDIT_LOG].find_one({"action": "tournament.register"})
    assert (entry["target"], entry["details"]["tournament"]) == (bot["_id"], "Pokal")
    assert deregister(owner_client, tournament, bot).status_code == 204
    assert active(db, tournament, bot) is None


def test_leaving_a_running_edition_forfeits_the_waiting_games(login, db):
    client, user = login()
    bot = own_bot(db, user)
    others = [own_bot(db, user, name) for name in ("Alpha", "Beta")]
    tournament = store_tournament(db)
    edition = start_edition(db, tournament, [*others, bot])

    response = deregister(client, tournament, bot)

    assert response.status_code == 204
    assert editions.get(db, edition["_id"])["withdrawn"] == [bot["_id"]]
    own = list(db[MATCHES].find(matches.match_filter(bot_id=bot["_id"])))
    assert own
    assert {game["termination"] for game in own} == {matches.FORFEIT}
    assert deregister(client, tournament, bot).status_code == 404


def test_retiring_or_disabling_a_bot_ends_its_registrations(login, admin, db):
    client, user = login()
    retired, disabled = own_bot(db, user), own_bot(db, user, "Other")
    tournament = store_tournament(db)
    register(client, tournament, retired)
    register(client, tournament, disabled)

    client.patch(f"/api/v1/bots/{retired['_id']}", json={"status": bots.RETIRED}, headers=CSRF)
    admin.patch(
        f"/api/v1/admin/bots/{disabled['_id']}", json={"status": bots.DISABLED}, headers=CSRF
    )

    left = {entry["bot_id"]: entry for entry in db[REGISTRATIONS].find()}
    assert left[retired["_id"]]["left_reason"] == registrations.RETIRED
    assert left[disabled["_id"]]["left_reason"] == registrations.DISABLED


def test_deleting_a_bot_withdraws_it_and_its_games_stay_gone(login, admin, db):
    _, user = login()
    entrants = [own_bot(db, user, name) for name in ("Alpha", "Beta", "Gamma")]
    tournament = store_tournament(db)
    edition = start_edition(db, tournament, entrants)
    gone = entrants[2]

    response = admin.delete(f"/api/v1/admin/bots/{gone['_id']}", headers=CSRF)

    assert response.status_code == 204
    assert editions.get(db, edition["_id"])["withdrawn"] == [gone["_id"]]
    assert db[MATCHES].count_documents(matches.match_filter(bot_id=gone["_id"])) == 0
    shown = admin.get(f"/api/v1/editions/{edition['_id']}").json
    assert shown["games"] == 2
    assert [row["withdrawn"] for row in shown["table"]] == [False, False, True]
