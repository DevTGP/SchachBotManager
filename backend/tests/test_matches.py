from datetime import timedelta

from bson import ObjectId
from sbm_store import matches

from stored_games import NOW, finish_by_resignation, start_with_opening


def test_lists_matches_newest_first_with_total(client, enqueue):
    older = enqueue(now=NOW - timedelta(minutes=5))
    newer = enqueue(now=NOW)
    response = client.get("/api/v1/matches?limit=1")
    assert response.status_code == 200
    assert response.json["total"] == 2
    assert [match["id"] for match in response.json["items"]] == [str(newer)]
    response = client.get("/api/v1/matches?limit=1&offset=1")
    assert [match["id"] for match in response.json["items"]] == [str(older)]


def test_summary_counts_moves_without_listing_them(client, db, enqueue):
    match_id = enqueue()
    start_with_opening(db, match_id, NOW)
    item = client.get("/api/v1/matches").json["items"][0]
    assert item["status"] == "running"
    assert item["ply_count"] == 2
    assert "moves" not in item
    assert item["discipline"]["name"] == "Blitz"
    assert item["started_at"] == "2026-05-01T12:00:00.000Z"


def test_filters_by_status_and_bot(client, db, enqueue, reference_bots):
    finished = enqueue()
    finish_by_resignation(db, finished, NOW)
    enqueue()
    response = client.get("/api/v1/matches?status=finished")
    assert [match["id"] for match in response.json["items"]] == [str(finished)]
    bot_id = reference_bots[1]["_id"]
    assert client.get(f"/api/v1/matches?bot_id={bot_id}").json["total"] == 2
    assert client.get(f"/api/v1/matches?bot_id={ObjectId()}").json["total"] == 0


def test_rejects_invalid_parameters(client):
    for query, field in [
        ("status=paused", "status"),
        ("limit=0", "limit"),
        ("limit=101", "limit"),
        ("offset=-1", "offset"),
        ("offset=1e3", "offset"),
        ("bot_id=xyz", "bot_id"),
    ]:
        response = client.get(f"/api/v1/matches?{query}")
        assert response.status_code == 400, query
        assert response.json["code"] == "invalid_parameter"
        assert response.json["field"] == field


def test_shows_a_finished_match_with_moves(client, db, enqueue):
    match_id = enqueue()
    finish_by_resignation(db, match_id, NOW)
    match = client.get(f"/api/v1/matches/{match_id}").json
    assert match["result"] == "1-0"
    assert match["termination"] == "resignation"
    assert match["white"]["sdk"] == "python-0.1.0"
    assert [move["san"] for move in match["moves"]] == ["e4", "e5"]
    assert match["moves"][0]["info"] == {"depth": 3, "score_cp": 20}
    assert "termination_detail" not in match


def test_aborted_match_hides_its_detail(client, db, enqueue):
    match_id = enqueue()
    matches.abort(db, match_id, "runner crashed: secret path", NOW)
    match = client.get(f"/api/v1/matches/{match_id}").json
    assert match["status"] == "aborted"
    assert match["result"] == "*"
    assert "secret" not in str(match)


def test_unknown_match_is_not_found(client):
    response = client.get(f"/api/v1/matches/{ObjectId()}")
    assert response.status_code == 404
    assert response.json["code"] == "not_found"
