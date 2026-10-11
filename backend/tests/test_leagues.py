"""GET /leagues, /leagues/{league_id}, /seasons/{season_id} and the league of a match (E137)."""

from bson import ObjectId
from sbm_store import matches, seasons
from sbm_store.names import MATCHES

from stored_games import NOW
from stored_leagues import register, start_season, store_league


def test_leagues_are_listed_by_name(client, db):
    store_league(db, "Zeta")
    store_league(db, "Alpha")

    response = client.get("/api/v1/leagues")

    assert [league["name"] for league in response.json["items"]] == ["Alpha", "Zeta"]


def test_a_league_shows_its_seasons_and_registrations(client, db, reference_bots):
    league = store_league(db)
    register(db, league, list(reference_bots))

    response = client.get(f"/api/v1/leagues/{league['_id']}")

    assert response.status_code == 200
    assert response.json["registered"] == 2
    assert [season["number"] for season in response.json["seasons"]] == [1]
    registered = response.json["registrations"]
    assert [entry["bot"]["name"] for entry in registered] == ["Random", "Material"]
    assert {entry["tier"] for entry in registered} == {None}
    assert client.get(f"/api/v1/leagues/{ObjectId()}").status_code == 404


def test_a_running_season_shows_its_table_and_tiers(client, db, reference_bots):
    league = store_league(db)
    season = start_season(db, league, list(reference_bots))

    response = client.get(f"/api/v1/seasons/{season['_id']}")
    detail = client.get(f"/api/v1/leagues/{league['_id']}").json

    assert response.status_code == 200
    assert response.json["status"] == "running"
    assert response.json["league_name"] == "Liga"
    assert response.json["discipline"]["name"] == "Liga Blitz"
    (tier,) = response.json["tiers"]
    assert (tier["tier"], tier["games"], tier["finished"]) == (1, 2, 0)
    assert [row["rank"] for row in tier["table"]] == [1, 2]
    assert {entry["tier"] for entry in detail["registrations"]} == {1}
    assert detail["season"]["participants"] == 2


def test_a_planned_season_has_no_tables(client, db):
    league = store_league(db)

    season = seasons.latest(db, league["_id"])
    response = client.get(f"/api/v1/seasons/{season['_id']}")

    assert (response.json["settings"], response.json["tiers"]) == (None, [])
    assert client.get(f"/api/v1/seasons/{ObjectId()}").status_code == 404


def test_league_games_carry_their_place_and_can_be_filtered(client, db, reference_bots):
    league = store_league(db)
    season = start_season(db, league, list(reference_bots))

    response = client.get(f"/api/v1/matches?season_id={season['_id']}&tier=1")
    others = client.get(f"/api/v1/matches?season_id={season['_id']}&tier=2")
    bots_only = client.get("/api/v1/matches?kind=bots")

    assert response.json["total"] == 2
    place = response.json["items"][0]["league"]
    assert place["league_name"] == "Liga"
    assert (place["season_number"], place["tier"], place["board"]) == (1, 1, 1)
    assert others.json["total"] == 0
    assert bots_only.json["total"] == 2


def test_a_tier_needs_a_season(client):
    response = client.get("/api/v1/matches?tier=1")

    assert (response.status_code, response.json["field"]) == (400, "tier")


def test_a_finished_season_shows_the_final_table(client, db, reference_bots):
    league = store_league(db)
    season = start_season(db, league, list(reference_bots))
    white_wins = {"status": matches.FINISHED, "result": "1-0", "termination": "checkmate"}
    db[MATCHES].update_many({"context.season_id": season["_id"]}, {"$set": white_wins})
    final = [{"tier": 1, "table": []}]
    assert seasons.finish(db, season["_id"], final, NOW)

    response = client.get(f"/api/v1/seasons/{season['_id']}")

    (tier,) = response.json["tiers"]
    assert (tier["games"], tier["finished"], tier["table"]) == (2, 2, [])
