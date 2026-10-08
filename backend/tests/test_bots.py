from bson import ObjectId
from sbm_store import bots

from bot_uploads import store_bot, verify


def test_lists_verified_bots_by_name(client, db, reference_bots):
    store_bot(db, ObjectId(), name="Pending")
    response = client.get("/api/v1/bots")
    assert response.status_code == 200
    assert [bot["name"] for bot in response.json["items"]] == ["Material", "Random"]
    assert all(bot["builtin"] for bot in response.json["items"])


def test_lists_every_verified_version(client, db):
    owner = ObjectId()
    verify(db, store_bot(db, owner, version="1.0.0"))
    verify(db, store_bot(db, owner, version="1.1.0"))
    response = client.get("/api/v1/bots")
    assert [(bot["name"], bot["version"]) for bot in response.json["items"]] == [
        ("Material", "1.0.0"),
        ("Random", "1.0.0"),
        ("Sharp", "1.0.0"),
        ("Sharp", "1.1.0"),
    ]


def test_shows_one_bot(client, reference_bots):
    random_bot = reference_bots[0]
    response = client.get(f"/api/v1/bots/{random_bot['_id']}")
    assert response.status_code == 200
    assert response.json["name"] == "Random"
    assert response.json["version"] == "1.0.0"
    assert response.json["status"] == bots.VERIFIED
    assert response.json["details"] is None
    assert "source_ref" not in response.json


def test_a_bot_in_verification_is_hidden_from_others(client, db, login):
    _, user = login()
    other, _ = login("other")
    bot = store_bot(db, user["_id"])
    assert client.get(f"/api/v1/bots/{bot['_id']}").status_code == 404
    assert other.get(f"/api/v1/bots/{bot['_id']}").status_code == 404


def test_the_owner_sees_the_report(db, login):
    owner, user = login()
    bot = verify(db, store_bot(db, user["_id"]), passed=False)

    response = owner.get(f"/api/v1/bots/{bot['_id']}")

    assert response.status_code == 200
    assert response.json["status"] == bots.REJECTED
    details = response.json["details"]
    assert details["rejection"] == {"stage": "analysis", "reason": "1 finding"}
    assert (details["rejected_at"], details["verified_at"]) == ("2026-05-01T12:00:00.000Z", None)
    assert (details["sdk_version"], details["runtime_version"]) == ("0.4.0", "3.12.1")
    report = details["report"]
    assert (report["result"], report["ruleset"]) == ("failed", "python-1")
    assert report["stages"][0]["findings"] == [
        {"rule": "import", "file": "bot.py", "line": 1, "message": "socket is not allowed"}
    ]


def test_admins_see_the_details_of_any_bot(admin, db, reference_bots):
    bot = store_bot(db, ObjectId())
    response = admin.get(f"/api/v1/bots/{bot['_id']}")
    assert response.json["details"]["owner"] is None
    assert response.json["details"]["files"][0]["path"] == "bot.py"

    builtin = admin.get(f"/api/v1/bots/{reference_bots[0]['_id']}").json["details"]
    assert (builtin["owner"], builtin["entry"], builtin["files"]) == (None, None, [])


def test_a_disabled_bot_stays_public(client, db):
    bot = verify(db, store_bot(db, ObjectId()))
    bots.set_enabled(db, bot["_id"], False)

    response = client.get(f"/api/v1/bots/{bot['_id']}")

    assert response.status_code == 200
    assert (response.json["status"], response.json["details"]) == (bots.DISABLED, None)
    assert client.get("/api/v1/bots").json["items"] == []


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
