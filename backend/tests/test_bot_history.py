"""GET /bots/{bot_id}/seasons, /rating-history and /record (E139-E141)."""

from dataclasses import replace

import pytest
from bson import ObjectId
from sbm_store import matches
from sbm_store.discipline import STANDARD_FEN
from sbm_store.enqueue import enqueue_match
from sbm_store.ratings import count_pending

from bot_uploads import store_bot
from stored_disciplines import store_discipline
from stored_games import BLITZ, NOW
from stored_leagues import start_season, store_league


def play(db, white, black, result: str, discipline=BLITZ):
    match_id = enqueue_match(db, white, black, discipline, start_fen=STANDARD_FEN, now=NOW)
    matches.start(db, match_id, NOW)
    matches.finish(
        db, match_id, sides={}, result=result, termination="checkmate", detail="", now=NOW
    )
    return match_id


def stored(db, name: str):
    discipline = store_discipline(db, name)
    return replace(BLITZ, name=name, discipline_id=discipline["_id"])


def test_the_seasons_of_a_bot_version(client, db, reference_bots):
    random, material = reference_bots
    season = start_season(db, store_league(db), [random, material])

    response = client.get(f"/api/v1/bots/{random['_id']}/seasons")

    assert response.status_code == 200
    (entry,) = response.json["items"]
    assert entry["season_id"] == str(season["_id"])
    assert (entry["league_name"], entry["number"], entry["status"]) == ("Liga", 1, "running")
    assert (entry["tier"], entry["tier_size"], entry["games"], entry["points"]) == (1, 2, 0, 0)
    assert (entry["finished_at"], entry["withdrawn"], entry["outcome"]) == (None, False, None)
    assert entry["rank"] in (1, 2)


def test_the_rating_history_per_discipline(client, db, reference_bots):
    random, material = reference_bots
    blitz, rapid = stored(db, "Blitz"), stored(db, "Rapid")
    first = play(db, random, material, "1-0", blitz)
    play(db, material, random, "1-0", blitz)
    play(db, material, random, "1/2-1/2", rapid)
    play(db, random, material, "1-0")
    assert count_pending(db) == 3

    response = client.get(f"/api/v1/bots/{random['_id']}/rating-history")

    assert response.status_code == 200
    assert [item["name"] for item in response.json["items"]] == ["Blitz", "Rapid"]
    games = response.json["items"][0]["games"]
    assert games[0]["match_id"] == str(first)
    assert (games[0]["before"], games[0]["after"]) == (2500, 2550)
    assert games[1]["before"] == 2550 > games[1]["after"]


def test_the_record_with_free_times_last(client, db, reference_bots):
    random, material = reference_bots
    blitz = stored(db, "Blitz")
    for result in ("1-0", "1/2-1/2", "0-1"):
        play(db, random, material, result, blitz)
    play(db, material, random, "0-1")

    response = client.get(f"/api/v1/bots/{random['_id']}/record")

    assert response.json == {
        "total": {"games": 4, "wins": 2, "draws": 1, "losses": 1},
        "disciplines": [
            {
                "discipline_id": str(blitz.discipline_id),
                "name": "Blitz",
                "games": 3,
                "wins": 1,
                "draws": 1,
                "losses": 1,
            },
            {"discipline_id": None, "name": None, "games": 1, "wins": 1, "draws": 0, "losses": 0},
        ],
    }


def test_a_bot_without_history(client, reference_bots):
    path = f"/api/v1/bots/{reference_bots[0]['_id']}"

    assert client.get(f"{path}/seasons").json == {"items": []}
    assert client.get(f"{path}/rating-history").json == {"items": []}
    assert client.get(f"{path}/record").json == {
        "total": {"games": 0, "wins": 0, "draws": 0, "losses": 0},
        "disciplines": [],
    }


@pytest.mark.parametrize("part", ["seasons", "rating-history", "record"])
def test_hidden_and_unknown_bots(client, db, part):
    hidden = store_bot(db, ObjectId())
    assert client.get(f"/api/v1/bots/{hidden['_id']}/{part}").status_code == 404
    assert client.get(f"/api/v1/bots/{ObjectId()}/{part}").status_code == 404
    assert client.get(f"/api/v1/bots/xyz/{part}").status_code == 400
