from sbm_store.names import USERS

from stored_disciplines import store_discipline


def test_an_account_without_rated_games_stands_at_the_start(login):
    client, _ = login("anna", "player")

    response = client.get("/api/v1/account/rating")

    assert response.status_code == 200
    assert response.json == {"value": 2500, "games": 0, "disciplines": []}


def test_the_account_sees_its_counted_rating(login, db):
    client, user = login()
    rapid = store_discipline(db, "Rapid")
    blitz = store_discipline(db, "Blitz", archived=True)
    store_discipline(db, "Bullet")
    entries = {
        str(rapid["_id"]): {"value": 2600, "games": 1, "seq": 9},
        str(blitz["_id"]): {"value": 2500, "games": 3, "seq": 8},
    }
    db[USERS].update_one({"_id": user["_id"]}, {"$set": {"ratings": entries}})

    # The overall rating weighs each discipline by its games (E163); the disciplines come by
    # name, archived ones included, unplayed ones left out (E169).
    assert client.get("/api/v1/account/rating").json == {
        "value": 2525,
        "games": 4,
        "disciplines": [
            {"discipline_id": str(blitz["_id"]), "name": "Blitz", "value": 2500, "games": 3},
            {"discipline_id": str(rapid["_id"]), "name": "Rapid", "value": 2600, "games": 1},
        ],
    }


def test_a_guest_has_no_rating(client):
    response = client.get("/api/v1/account/rating")

    assert response.status_code == 401
    assert response.json["code"] == "unauthenticated"
