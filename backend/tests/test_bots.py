from bson import ObjectId
from sbm_store import bots
from sbm_store.names import BOTS

from stored_games import NOW


def test_lists_verified_bots_by_name(client, db, reference_bots):
    db[BOTS].insert_one(
        {
            "_id": ObjectId(),
            "name": "Pending",
            "language": "python",
            "source_ref": "uploads/x",
            "status": "checking",
            "created_at": NOW,
        }
    )
    response = client.get("/api/v1/bots")
    assert response.status_code == 200
    assert [bot["name"] for bot in response.json["items"]] == ["Material", "Random"]
    assert all(bot["builtin"] for bot in response.json["items"])


def test_shows_one_bot(client, reference_bots):
    random_bot = reference_bots[0]
    response = client.get(f"/api/v1/bots/{random_bot['_id']}")
    assert response.status_code == 200
    assert response.json["name"] == "Random"
    assert response.json["status"] == bots.VERIFIED
    assert "source_ref" not in response.json


def test_unknown_bot_is_not_found(client, reference_bots):
    response = client.get(f"/api/v1/bots/{ObjectId()}")
    assert response.status_code == 404
    assert response.json["code"] == "not_found"


def test_malformed_bot_id_is_invalid(client):
    response = client.get("/api/v1/bots/ABC")
    assert response.status_code == 400
    assert response.json == {
        "code": "invalid_parameter",
        "message": "bot_id must be 24 lowercase hexadecimal digits",
        "field": "bot_id",
    }
