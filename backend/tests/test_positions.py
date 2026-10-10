"""POST /positions/from-pgn: a start position from a recorded game (E159)."""

import pytest

from accounts import CSRF

PGN = """[Event "One"]
[Result "*"]

1. e4 e5 2. Nf3 *

[Event "Two"]
[Result "*"]

1. d4 *
"""
AFTER_E4 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
AFTER_D4 = "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1"


def position(client, **body):
    return client.post("/api/v1/positions/from-pgn", json=body, headers=CSRF)


def test_the_position_after_some_half_moves(login):
    coder, _ = login()

    assert position(coder, pgn=PGN, plies=1).json == {"fen": AFTER_E4}
    assert position(coder, pgn=PGN, game=2).json == {"fen": AFTER_D4}


@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({"pgn": "1. e4 e9 *"}, "pgn"),
        ({"pgn": ""}, "pgn"),
        ({"pgn": PGN, "game": 3}, "game"),
        ({"pgn": PGN, "game": 0}, "game"),
        ({"pgn": PGN, "plies": 4}, "plies"),
        ({"pgn": PGN, "plies": -1}, "plies"),
        ({"pgn": PGN, "colour": "white"}, "colour"),
    ],
)
def test_invalid_requests(login, body, field):
    coder, _ = login()

    response = position(coder, **body)

    assert (response.status_code, response.json["field"]) == (400, field)


def test_needs_a_coder(client, login):
    player, _ = login("pat", "player")
    assert position(client, pgn=PGN).status_code == 401
    assert position(player, pgn=PGN).status_code == 403
