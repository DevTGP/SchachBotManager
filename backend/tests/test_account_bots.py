from datetime import timedelta

from bson import ObjectId

from bot_uploads import store_bot, verify
from stored_games import NOW


def test_lists_the_own_bots_newest_first(login, db):
    coder, user = login()
    verify(db, store_bot(db, user["_id"], version="1.0.0"))
    store_bot(db, user["_id"], version="1.1.0", now=NOW + timedelta(minutes=1))
    store_bot(db, ObjectId(), name="Foreign")

    response = coder.get("/api/v1/account/bots")

    assert response.status_code == 200
    assert [(bot["version"], bot["status"]) for bot in response.json["items"]] == [
        ("1.1.0", "uploaded"),
        ("1.0.0", "verified"),
    ]


def test_needs_an_account(client):
    assert client.get("/api/v1/account/bots").status_code == 401
