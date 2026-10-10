"""GET /matches filtered by discipline, opponent and requester (E160, E161)."""

from bson import ObjectId
from sbm.referee import STANDARD_FEN
from sbm_store import disciplines
from sbm_store.enqueue import enqueue_match

from accounts import CSRF
from bot_uploads import store_bot, verify
from stored_disciplines import store_discipline
from stored_games import NOW


def ids(response) -> list[str]:
    return [match["id"] for match in response.json["items"]]


def test_by_discipline(client, db, reference_bots, enqueue):
    rapid = store_discipline(db, "Rapid")
    rated = enqueue_match(
        db, *reference_bots, disciplines.snapshot(rapid), start_fen=STANDARD_FEN, now=NOW
    )
    enqueue()

    response = client.get(f"/api/v1/matches?discipline_id={rapid['_id']}")

    assert ids(response) == [str(rated)]
    assert client.get("/api/v1/matches?discipline_id=xyz").status_code == 400


def test_by_opponent(client, db, reference_bots, enqueue):
    random, material = reference_bots
    other = verify(db, store_bot(db, ObjectId(), name="Other"))
    against = enqueue()
    enqueue_match(
        db,
        random,
        other,
        disciplines.snapshot(store_discipline(db, "Rapid")),
        start_fen=STANDARD_FEN,
        now=NOW,
    )

    pair = client.get(f"/api/v1/matches?bot_id={random['_id']}&opponent_id={material['_id']}")
    turned = client.get(f"/api/v1/matches?bot_id={material['_id']}&opponent_id={random['_id']}")

    assert ids(pair) == ids(turned) == [str(against)]
    assert client.get(f"/api/v1/matches?bot_id={random['_id']}").json["total"] == 2
    alone = client.get(f"/api/v1/matches?opponent_id={material['_id']}")
    assert (alone.status_code, alone.json["field"]) == (400, "opponent_id")


def test_games_set_by_the_account(login, client, db, reference_bots, enqueue):
    coder, user = login()
    bot = verify(db, store_bot(db, user["_id"]))
    data = {
        "white_bot_id": str(bot["_id"]),
        "black_bot_id": str(reference_bots[0]["_id"]),
        "initial_time_ms": 60_000,
    }
    own = coder.post("/api/v1/matches", json=data, headers=CSRF).json["match_ids"]
    enqueue()

    assert ids(coder.get("/api/v1/matches?mine=true")) == own
    assert coder.get("/api/v1/matches?mine=false").json["total"] == 2
    assert coder.get("/api/v1/matches?mine=yes").status_code == 400
    assert client.get("/api/v1/matches?mine=true").status_code == 401
