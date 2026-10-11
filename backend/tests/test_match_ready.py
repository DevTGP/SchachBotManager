"""POST /matches/{match_id}/ready and GET /account/competition-games (E183, E186)."""

from datetime import timedelta

from bson import ObjectId
from sbm_store import competition_readiness, matches, tokens

from accounts import CSRF
from stored_games import NOW
from stored_leagues import start_season, store_league


def season_with(db, user, bot):
    """A running season of the account and the bot; its first game is released."""
    season = start_season(db, store_league(db), [bot, user])
    released = competition_readiness.release(db, NOW)
    assert len(released) == 1
    return season, released[0]


def ready(client, match_id, **body):
    return client.post(f"/api/v1/matches/{match_id}/ready", json=body or None, headers=CSRF)


def test_the_own_games_released_first_with_readiness(login, db, reference_bots):
    client, user = login("pat", "player")
    _, released = season_with(db, user, reference_bots[0])

    items = client.get("/api/v1/account/competition-games").json["items"]

    assert [item["match"]["id"] for item in items][0] == str(released)
    assert len(items) == 2
    first, second = items
    readiness = first["match"]["readiness"]
    assert readiness["deadline"] is not None
    assert readiness["started_at"] is None
    assert readiness[first["color"]] == {"ready": False, "present": False}
    assert readiness["white" if first["color"] == "black" else "black"] is None
    assert second["match"]["readiness"] is None
    assert login("other")[0].get("/api/v1/account/competition-games").json["items"] == []


def test_ready_hands_out_a_seat_and_keeps_it(login, db, reference_bots, clock):
    client, user = login("pat", "player")
    _, match_id = season_with(db, user, reference_bots[0])

    first = ready(client, match_id)
    clock.advance(timedelta(seconds=15))
    kept = ready(client, match_id, seat=first.json["seat"])
    replaced = ready(client, match_id, seat="x" * 43)

    assert first.status_code == 200
    color = first.json["color"]
    assert first.json["socket_path"] == "/api/v1/play/socket"
    assert kept.json["seat"] == first.json["seat"]
    assert replaced.json["seat"] != first.json["seat"]
    match = matches.get(db, match_id)
    assert match[color]["seat_hash"] == tokens.token_hash(replaced.json["seat"])
    assert match["readiness"][color]["ready_at"] == NOW
    assert match["readiness"][color]["seen_at"] == NOW + timedelta(seconds=15)
    shown = client.get(f"/api/v1/matches/{match_id}").json["readiness"][color]
    assert shown == {"ready": True, "present": True}


def test_ready_only_for_the_own_released_waiting_game(login, client, db, reference_bots):
    player, user = login("pat", "player")
    _, match_id = season_with(db, user, reference_bots[0])
    other, _ = login("other")
    waiting = next(
        item["match"]["id"]
        for item in player.get("/api/v1/account/competition-games").json["items"]
        if item["match"]["readiness"] is None
    )

    assert client.post(f"/api/v1/matches/{match_id}/ready", headers=CSRF).status_code == 401
    assert ready(other, match_id).status_code == 403
    assert ready(player, ObjectId()).status_code == 404
    assert ready(player, match_id, seat="short").json["field"] == "seat"
    refused = ready(player, waiting)
    assert (refused.status_code, refused.json["code"]) == (409, "match_state")
    competition_readiness.expire(db, NOW + timedelta(days=30))
    assert ready(player, match_id).json["code"] == "match_state"
