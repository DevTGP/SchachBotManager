"""GET /seasons/{season_id}/schedule: the rounds of one tier with their games (E138)."""

from bson import ObjectId
from sbm_store import matches, seasons
from sbm_store.names import MATCHES

from stored_leagues import start_season, store_league


def test_the_rounds_of_a_tier_by_board(client, db, reference_bots):
    random, material = reference_bots
    season = start_season(db, store_league(db), [random, material])
    first = db[MATCHES].find_one({"context.season_id": season["_id"], "context.round": 1})
    db[MATCHES].update_one(
        {"_id": first["_id"]},
        {"$set": {"status": matches.FINISHED, "result": "0-1", "termination": matches.FORFEIT}},
    )

    response = client.get(f"/api/v1/seasons/{season['_id']}/schedule?tier=1")

    assert response.status_code == 200
    assert response.json["tier"] == 1
    assert [each["round"] for each in response.json["rounds"]] == [1, 2]
    assert {each["bye"] for each in response.json["rounds"]} == {None}
    (game,) = response.json["rounds"][0]["games"]
    assert game["match_id"] == str(first["_id"])
    assert (game["board"], game["status"], game["result"]) == (1, "finished", "0-1")
    assert game["termination"] == "forfeit_withdrawn"
    assert {game["white"]["name"], game["black"]["name"]} == {"Random", "Material"}
    (waiting,) = response.json["rounds"][1]["games"]
    assert (waiting["status"], waiting["result"], waiting["termination"]) == ("queued", None, None)


def test_unknown_seasons_and_tiers(client, db, reference_bots):
    season = start_season(db, store_league(db), list(reference_bots))
    planned = seasons.latest(db, store_league(db, "Andere")["_id"])
    path = f"/api/v1/seasons/{season['_id']}/schedule"

    assert client.get(f"{path}?tier=2").status_code == 404
    assert client.get(f"/api/v1/seasons/{planned['_id']}/schedule?tier=1").status_code == 404
    assert client.get(f"/api/v1/seasons/{ObjectId()}/schedule?tier=1").status_code == 404
    assert client.get(path).status_code == 400
    assert client.get(f"{path}?tier=0").status_code == 400
    assert client.get("/api/v1/seasons/xyz/schedule?tier=1").status_code == 400
