from bson import ObjectId

from stored_games import NOW, SITE, finish_by_resignation, start_with_opening

ENDGAME = "8/8/8/4k3/8/8/4P3/4K3 w - - 0 1"


def test_finished_match_as_pgn(client, db, enqueue):
    match_id = enqueue()
    finish_by_resignation(db, match_id, NOW)
    response = client.get(f"/api/v1/matches/{match_id}/pgn")
    assert response.status_code == 200
    assert response.mimetype == "application/x-chess-pgn"
    assert f'filename="match-{match_id}.pgn"' in response.headers["Content-Disposition"]
    text = response.get_data(as_text=True)
    assert f'[Site "{SITE}"]' in text
    assert '[Date "2026.05.01"]' in text
    assert '[White "Random"]' in text
    assert '[TimeControl "180+2"]' in text
    assert '[Termination "normal"]' in text
    assert "SetUp" not in text
    assert text.rstrip().endswith("1. e4 e5 {resignation} 1-0")
    assert "black resigned" not in text


def test_running_match_is_unterminated(client, db, enqueue):
    match_id = enqueue(start_fen=ENDGAME)
    start_with_opening(db, match_id, NOW)
    text = client.get(f"/api/v1/matches/{match_id}/pgn").get_data(as_text=True)
    assert '[Result "*"]' in text
    assert '[Termination "unterminated"]' in text
    assert f'[FEN "{ENDGAME}"]' in text
    assert text.rstrip().endswith("*")


def test_pgn_of_unknown_match_is_not_found(client):
    assert client.get(f"/api/v1/matches/{ObjectId()}/pgn").status_code == 404
