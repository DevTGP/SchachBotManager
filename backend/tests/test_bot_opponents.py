"""GET /bots/{bot_id}/opponents: the record of a bot against each other bot (E161)."""

from bson import ObjectId
from sbm_store import matches

from bot_uploads import store_bot
from stored_games import NOW


def finish(db, match_id, result: str) -> None:
    matches.start(db, match_id, NOW)
    matches.finish(
        db, match_id, sides={}, result=result, termination="checkmate", detail="", now=NOW
    )


def test_wins_draws_and_losses_per_opponent(client, db, reference_bots, enqueue):
    random, material = reference_bots
    for result in ("1-0", "1/2-1/2", "0-1", "0-1"):
        finish(db, enqueue(), result)
    enqueue()

    response = client.get(f"/api/v1/bots/{material['_id']}/opponents")

    assert response.status_code == 200
    assert response.json == {
        "items": [
            {
                "bot_id": str(random["_id"]),
                "name": "Random",
                "version": random.get("version"),
                "games": 4,
                "wins": 2,
                "draws": 1,
                "losses": 1,
            }
        ]
    }


def test_a_bot_without_games(client, reference_bots):
    response = client.get(f"/api/v1/bots/{reference_bots[0]['_id']}/opponents")
    assert response.json == {"items": []}


def test_hidden_and_unknown_bots(client, db):
    hidden = store_bot(db, ObjectId())
    assert client.get(f"/api/v1/bots/{hidden['_id']}/opponents").status_code == 404
    assert client.get(f"/api/v1/bots/{ObjectId()}/opponents").status_code == 404
    assert client.get("/api/v1/bots/xyz/opponents").status_code == 400
