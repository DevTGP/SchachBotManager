"""POST and PATCH /admin/leagues and POST /admin/leagues/{league_id}/start (E131, E132)."""

import pytest
from bson import ObjectId
from sbm_store import leagues, seasons
from sbm_store.names import AUDIT_LOG

from accounts import CSRF
from stored_disciplines import store_discipline
from stored_games import NOW
from stored_leagues import store_league


def create(client, discipline: dict, **body):
    request = {"name": "Liga", "discipline_id": str(discipline["_id"])} | body
    return client.post("/api/v1/admin/leagues", json=request, headers=CSRF)


def update(client, league_id, **body):
    return client.patch(f"/api/v1/admin/leagues/{league_id}", json=body, headers=CSRF)


def start(client, league_id):
    return client.post(f"/api/v1/admin/leagues/{league_id}/start", headers=CSRF)


def test_create_with_defaults_a_planned_season_and_an_audit_entry(admin, db):
    blitz = store_discipline(db, "Blitz")

    response = create(admin, blitz, name="  Liga  ", tiers=2, tier_size=4)

    assert response.status_code == 201
    league = response.json
    assert (league["name"], league["discipline_name"]) == ("Liga", "Blitz")
    assert (league["tiers"], league["tier_size"], league["promotions"]) == (2, 4, 2)
    assert league["points"] == {"win": 1, "draw": 0.5, "loss": 0}
    assert league["tiebreaks"] == ["wins", "head_to_head", "sonneborn_berger"]
    assert (league["archived"], league["registered"]) == (False, 0)
    assert league["season"]["number"] == 1
    assert league["season"]["status"] == "planned"
    assert league["season"]["starts_after"] is None
    entry = db[AUDIT_LOG].find_one({"action": "league.create"})
    assert entry["target"] == ObjectId(league["id"])


def test_names_are_unique_regardless_of_case(admin, db):
    blitz = store_discipline(db, "Blitz")
    create(admin, blitz)

    response = create(admin, blitz, name="LIGA")

    assert (response.status_code, response.json["code"]) == (409, "name_taken")


@pytest.mark.parametrize(
    "body",
    [
        {"points": {"win": 1, "draw": 2, "loss": 0}},
        {"points": {"win": 0, "draw": 0, "loss": 0}},
        {"points": {"win": 1.25, "draw": 0.5, "loss": 0}},
        {"points": {"win": 1, "draw": 0.5}},
        {"tiebreaks": ["wins", "wins"]},
        {"tiebreaks": ["coin"]},
        {"tier_size": 4, "promotions": 3},
        {"tiers": 0},
        {"name": "x" * 41},
        {"colour": "blue"},
    ],
)
def test_invalid_settings_are_refused(admin, db, body):
    blitz = store_discipline(db, "Blitz")

    response = create(admin, blitz, **body)

    assert (response.status_code, response.json["code"]) == (400, "invalid_parameter")


def test_an_archived_discipline_cannot_be_chosen(admin, db):
    old = store_discipline(db, "Alt", archived=True)

    response = create(admin, old)

    assert response.json["field"] == "discipline_id"


def test_update_checks_promotions_against_the_stored_tier_size(admin, db):
    league = store_league(db, tier_size=4)

    refused = update(admin, league["_id"], promotions=3)
    changed = update(admin, league["_id"], name="Neu", promotions=2, archived=True)

    assert refused.json["field"] == "promotions"
    assert changed.status_code == 200
    assert (changed.json["name"], changed.json["archived"]) == ("Neu", True)
    assert db[AUDIT_LOG].find_one({"action": "league.update"})["details"]["name"] == "Neu"


def test_update_refuses_a_taken_name_and_an_empty_body(admin, db):
    league = store_league(db)
    store_league(db, "Andere")

    assert update(admin, league["_id"], name="andere").json["code"] == "name_taken"
    assert update(admin, league["_id"]).json["code"] == "invalid_parameter"
    assert update(admin, ObjectId()).status_code == 404


def test_start_releases_the_first_season_once(admin, db, clock):
    league = store_league(db)

    first = start(admin, league["_id"])
    again = start(admin, league["_id"])

    assert first.status_code == 200
    assert seasons.latest(db, league["_id"])["starts_after"] == clock.now()
    assert (again.status_code, again.json["code"]) == (409, "league_state")
    assert db[AUDIT_LOG].count_documents({"action": "league.start"}) == 1


def test_an_archived_league_does_not_start(admin, db):
    league = store_league(db)
    leagues.update(db, league["_id"], {"archived": True}, now=NOW)

    response = start(admin, league["_id"])

    assert (response.status_code, response.json["code"]) == (409, "league_state")


def test_only_admins_manage_leagues(login, db):
    coder, _ = login()
    blitz = store_discipline(db, "Blitz")

    assert create(coder, blitz).status_code == 403
