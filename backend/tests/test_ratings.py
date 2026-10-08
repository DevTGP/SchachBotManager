from dataclasses import replace

from bson import ObjectId
from sbm.referee import STANDARD_FEN
from sbm_store import ratings
from sbm_store.enqueue import enqueue_match

from bot_uploads import store_bot
from stored_games import BLITZ, NOW, finish_by_resignation


def rated_win(db, white: dict, black: dict) -> ObjectId:
    """White wins a rated match, and the runner counts it."""
    discipline = replace(BLITZ, discipline_id=ObjectId())
    match_id = enqueue_match(db, white, black, discipline, start_fen=STANDARD_FEN, now=NOW)
    finish_by_resignation(db, match_id, NOW)
    ratings.count_pending(db)
    return match_id


def test_a_bot_starts_at_2500(client, reference_bots):
    items = client.get("/api/v1/bots").json["items"]
    assert [bot["rating"] for bot in items] == [{"value": 2500, "games": 0}] * 2


def test_the_ranking_is_empty_without_counted_matches(client, db, reference_bots):
    store_bot(db, ObjectId(), name="Pending")
    response = client.get("/api/v1/ratings")
    assert response.status_code == 200
    assert response.json["items"] == []


def test_the_ranking_holds_the_counted_bots_highest_first(client, db, reference_bots):
    random_bot, material = reference_bots
    rated_win(db, material, random_bot)
    items = client.get("/api/v1/ratings").json["items"]
    assert [(bot["name"], bot["rating"]) for bot in items] == [
        ("Material", {"value": 2550, "games": 1}),
        ("Random", {"value": 2450, "games": 1}),
    ]


def test_a_counted_match_shows_the_change_of_each_side(client, db, enqueue, reference_bots):
    match_id = rated_win(db, *reference_bots)
    unrated = enqueue()
    match = client.get(f"/api/v1/matches/{match_id}").json
    assert match["rated"]
    assert match["white"]["rating"] == {"before": 2500, "after": 2550}
    assert match["black"]["rating"] == {"before": 2500, "after": 2450}
    summary = client.get(f"/api/v1/matches?bot_id={reference_bots[0]['_id']}").json["items"]
    assert [item["white"]["rating"] for item in summary] == [None, {"before": 2500, "after": 2550}]
    assert client.get(f"/api/v1/matches/{unrated}").json["black"]["rating"] is None
    detail = client.get(f"/api/v1/bots/{reference_bots[1]['_id']}").json
    assert detail["rating"] == {"value": 2450, "games": 1}
