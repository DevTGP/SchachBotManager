"""A random bot in place of an id, drawn anew for every game (E162)."""

from bson import ObjectId
from sbm_store import bots, matches
from sbm_store.names import AUDIT_LOG, BOTS

from accounts import CSRF
from bot_uploads import store_bot, verify


def queued(db, response) -> list[dict]:
    return [matches.get(db, ObjectId(match_id)) for match_id in response.json["match_ids"]]


def admin_enqueue(admin, white, black, **body):
    request = {"white_bot_id": white, "black_bot_id": black, "initial_time_ms": 60_000} | body
    return admin.post("/api/v1/admin/matches", json=request, headers=CSRF)


def test_random_against_random_draws_two_bots_for_every_game(admin, db, reference_bots):
    verify(db, store_bot(db, ObjectId(), name="Sharp"))

    response = admin_enqueue(admin, "random", "random", games=10)

    assert response.status_code == 201, response.json
    assert response.json["series_id"] is None
    games = queued(db, response)
    assert len(games) == 10
    assert all(game["white"]["bot_id"] != game["black"]["bot_id"] for game in games)
    names = {game[color]["name"] for game in games for color in ("white", "black")}
    assert names <= {"Random", "Material", "Sharp"}
    assert all("series" not in game or game["series"] is None for game in games)
    entry = db[AUDIT_LOG].find_one({"action": "match.enqueue"})
    assert (entry["details"]["white"], entry["details"]["black"]) == ("random", "random")


def test_a_fixed_side_keeps_its_colour_or_alternates(admin, db, reference_bots):
    random_bot, material = reference_bots

    fixed = queued(db, admin_enqueue(admin, str(material["_id"]), "random", games=4))
    alternating = queued(
        db, admin_enqueue(admin, str(material["_id"]), "random", games=4, alternate=True)
    )

    assert {(game["white"]["name"], game["black"]["name"]) for game in fixed} == {
        ("Material", "Random")
    }
    assert [game["white"]["name"] for game in alternating] == ["Material", "Random"] * 2


def test_random_needs_enough_verified_bots(admin, db, reference_bots):
    random_bot, material = reference_bots
    db[BOTS].update_one({"_id": random_bot["_id"]}, {"$set": {"status": bots.DISABLED}})

    against_itself = admin_enqueue(admin, str(material["_id"]), "random")
    both = admin_enqueue(admin, "random", "random")

    assert (against_itself.status_code, against_itself.json["field"]) == (400, "black_bot_id")
    assert (both.status_code, both.json["field"]) == (400, "white_bot_id")


def test_other_words_are_no_bot(admin, reference_bots):
    response = admin_enqueue(admin, "any", str(reference_bots[0]["_id"]))

    assert (response.status_code, response.json["field"]) == (400, "white_bot_id")


def own_enqueue(client, white, black, **body):
    request = {"white_bot_id": white, "black_bot_id": black, "initial_time_ms": 60_000} | body
    return client.post("/api/v1/matches", json=request, headers=CSRF)


def test_a_coder_draws_a_random_opponent_for_the_own_bot(login, db, reference_bots):
    coder, user = login()
    own = verify(db, store_bot(db, user["_id"]))

    response = own_enqueue(coder, "random", str(own["_id"]), games=3)

    assert response.status_code == 201, response.json
    games = queued(db, response)
    assert all(game["black"]["bot_id"] == own["_id"] for game in games)
    assert {game["white"]["name"] for game in games} <= {"Random", "Material"}


def test_a_coder_cannot_draw_both_sides(login, db, reference_bots):
    coder, user = login()
    verify(db, store_bot(db, user["_id"]))

    response = own_enqueue(coder, "random", "random")
    foreign = own_enqueue(coder, "random", str(reference_bots[0]["_id"]))

    assert (response.status_code, response.json["field"]) == (400, "white_bot_id")
    assert (foreign.status_code, foreign.json["field"]) == (400, "white_bot_id")


def test_a_person_plays_a_random_bot(client, db, reference_bots):
    request = {"bot_id": "random", "color": "black", "initial_time_ms": 300_000}

    response = client.post("/api/v1/play", json=request, headers=CSRF)

    assert response.status_code == 201, response.json
    match = matches.get(db, ObjectId(response.json["match_id"]))
    assert match["white"]["name"] in {"Random", "Material"}


def test_bots_show_their_creator(login, client, db, reference_bots):
    _coder, user = login("alice")
    verify(db, store_bot(db, user["_id"]))

    items = client.get("/api/v1/bots").json["items"]

    assert {bot["name"]: bot["owner"] for bot in items} == {
        "Material": None,
        "Random": None,
        "Sharp": "alice",
    }
