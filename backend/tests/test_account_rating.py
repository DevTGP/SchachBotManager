from sbm_store.names import USERS


def test_an_account_without_rated_games_stands_at_the_start(login):
    client, _ = login("anna", "player")

    response = client.get("/api/v1/account/rating")

    assert response.status_code == 200
    assert response.json == {"value": 2500, "games": 0}


def test_the_account_sees_its_counted_rating(login, db):
    client, user = login()
    db[USERS].update_one(
        {"_id": user["_id"]}, {"$set": {"rating": {"value": 2547, "games": 3, "seq": 9}}}
    )

    assert client.get("/api/v1/account/rating").json == {"value": 2547, "games": 3}


def test_a_guest_has_no_rating(client):
    response = client.get("/api/v1/account/rating")

    assert response.status_code == 401
    assert response.json["code"] == "unauthenticated"
