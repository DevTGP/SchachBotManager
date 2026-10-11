"""GET /tournaments, /tournaments/{id}, /editions/{id}, /editions/{id}/rounds, the tournaments
and editions of a bot and the tournament of a match (E180)."""

from bson import ObjectId
from sbm_store import tournaments
from stored_tournaments import enter, finish_waiting, start_edition, store_tournament, tick

from bot_uploads import store_bot, verify


def some_bots(db, count: int) -> list[dict]:
    owner = ObjectId()
    return [verify(db, store_bot(db, owner, name=f"Bot{number}")) for number in range(count)]


def test_tournaments_are_listed_by_name_with_their_latest_edition(client, db):
    store_tournament(db, "Zeta")
    store_tournament(db, "Alpha", tournaments.KNOCKOUT)

    response = client.get("/api/v1/tournaments")

    items = response.json["items"]
    assert [each["name"] for each in items] == ["Alpha", "Zeta"]
    assert [each["format"] for each in items] == ["knockout", "round_robin"]
    assert {each["edition"]["status"] for each in items} == {"planned"}
    assert {each["recurrence"] for each in items} == {None}


def test_a_tournament_shows_its_editions_and_registrations(client, db):
    tournament = store_tournament(db)
    enter(db, tournament, some_bots(db, 2))

    response = client.get(f"/api/v1/tournaments/{tournament['_id']}")

    assert response.status_code == 200
    assert response.json["registered"] == 2
    assert [edition["number"] for edition in response.json["editions"]] == [1]
    registered = response.json["registrations"]
    assert [entry["bot"]["name"] for entry in registered] == ["Bot0", "Bot1"]
    assert {entry["playing"] for entry in registered} == {False}
    assert client.get(f"/api/v1/tournaments/{ObjectId()}").status_code == 404


def test_a_planned_edition_has_no_table(client, db):
    tournament = store_tournament(db)
    edition = client.get(f"/api/v1/tournaments/{tournament['_id']}").json["editions"][0]

    response = client.get(f"/api/v1/editions/{edition['id']}")

    assert response.json["status"] == "planned"
    assert (response.json["settings"], response.json["table"]) == (None, [])
    assert response.json["tournament_name"] == "Pokal"
    assert client.get(f"/api/v1/editions/{ObjectId()}").status_code == 404
    rounds = client.get(f"/api/v1/editions/{edition['id']}/rounds")
    assert rounds.json["rounds"] == []


def test_a_round_robin_edition_shows_its_table_and_rounds(client, db):
    entrants = some_bots(db, 3)
    tournament = store_tournament(db, games_per_pairing=1)
    edition = start_edition(db, tournament, entrants)
    finish_waiting(db, edition)
    tick(db)

    response = client.get(f"/api/v1/editions/{edition['_id']}")
    rounds = client.get(f"/api/v1/editions/{edition['_id']}/rounds")
    detail = client.get(f"/api/v1/tournaments/{tournament['_id']}").json

    assert response.status_code == 200
    assert response.json["status"] == "finished"
    assert (response.json["games"], response.json["finished"]) == (3, 3)
    assert [row["rank"] for row in response.json["table"]] == [1, 2, 3]
    assert response.json["bracket"] == []
    assert response.json["discipline"]["name"] == "Pokal Blitz"
    assert [each["round"] for each in rounds.json["rounds"]] == [1, 2, 3]
    assert {len(each["games"]) for each in rounds.json["rounds"]} == {1}
    assert {each["bye"] is None for each in rounds.json["rounds"]} == {False}
    latest, first = detail["editions"]
    assert (latest["number"], latest["status"]) == (2, "planned")
    assert first["winner"]["name"] == response.json["table"][0]["bot"]["name"]


def test_a_swiss_edition_gives_one_bot_a_bye(client, db):
    entrants = some_bots(db, 3)
    edition = start_edition(db, store_tournament(db, format=tournaments.SWISS, rounds=2), entrants)

    response = client.get(f"/api/v1/editions/{edition['_id']}/rounds")

    (first,) = response.json["rounds"]
    assert first["round"] == 1
    assert first["bye"] is not None
    assert len(first["games"]) == 1
    assert first["games"][0]["status"] == "queued"


def test_a_knockout_edition_shows_its_bracket(client, db):
    entrants = some_bots(db, 3)
    tournament = store_tournament(db, format=tournaments.KNOCKOUT, games_per_pairing=1)
    edition = start_edition(db, tournament, entrants)

    response = client.get(f"/api/v1/editions/{edition['_id']}")

    assert response.json["bracket_size"] == 4
    assert response.json["table"] == []
    bye, duel = response.json["bracket"]
    assert (bye["decided"], bye["decided_by"], bye["b"]) == (True, "bye", None)
    assert bye["winner"] == bye["a"]["bot"]["bot_id"]
    assert (duel["decided"], len(duel["games"])) == (False, 1)
    assert duel["games"][0]["phase"] == "regular"
    assert response.json["tiebreak_discipline"]["name"] == "Pokal Blitz"
    assert [each["place"] for each in response.json["placements"]] == [None, None, None]


def test_a_bot_lists_its_tournaments_and_editions(client, db):
    entrants = some_bots(db, 2)
    tournament = store_tournament(db)
    edition = start_edition(db, tournament, entrants)
    bot = entrants[0]

    registered = client.get(f"/api/v1/bots/{bot['_id']}/tournaments").json["items"]
    played = client.get(f"/api/v1/bots/{bot['_id']}/editions").json["items"]

    assert [(entry["tournament_name"], entry["playing"]) for entry in registered] == [
        ("Pokal", True)
    ]
    (entry,) = played
    assert (entry["edition_id"], entry["format"], entry["status"]) == (
        str(edition["_id"]),
        "round_robin",
        "running",
    )
    assert (entry["participants"], entry["withdrawn"]) == (2, False)
    assert client.get(f"/api/v1/bots/{ObjectId()}/editions").status_code == 404


def test_matches_name_their_tournament_and_filter_by_edition(client, db):
    entrants = some_bots(db, 2)
    edition = start_edition(db, store_tournament(db), entrants)

    response = client.get(f"/api/v1/matches?edition_id={edition['_id']}")

    items = response.json["items"]
    assert len(items) == 2
    place = items[0]["tournament"]
    assert (place["tournament_name"], place["edition_number"], place["format"]) == (
        "Pokal",
        1,
        "round_robin",
    )
    assert place["edition_id"] == str(edition["_id"])
    assert items[0]["league"] is None
    assert client.get("/api/v1/matches?edition_id=xyz").status_code == 400
