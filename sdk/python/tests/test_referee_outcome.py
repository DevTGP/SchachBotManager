"""Endings the referee scores by itself."""

import pytest

from sbm import BLACK, WHITE, Board
from sbm.referee.outcome import (
    Outcome,
    loss,
    position_outcome,
    startup_outcome,
    timeout_outcome,
)


def ending(fen: str, max_moves: int = 500, plies: int = 0):
    outcome = position_outcome(Board.from_fen(fen), max_moves, plies)
    return outcome and (outcome.result, outcome.termination, outcome.winner)


@pytest.mark.parametrize(
    ("fen", "expected"),
    [
        ("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3", ("0-1", "checkmate", 1)),
        ("k7/1Q6/1K6/8/8/8/8/8 b - - 0 1", ("1-0", "checkmate", 0)),
        ("k7/8/1Q6/8/8/8/8/7K b - - 0 1", ("1/2-1/2", "stalemate", None)),
        ("k7/8/8/8/8/8/8/6NK w - - 0 1", ("1/2-1/2", "insufficient_material", None)),
        ("k7/8/8/8/8/8/8/1R5K w - - 100 80", ("1/2-1/2", "fifty_move_rule", None)),
        ("k7/8/8/8/8/8/8/1R5K w - - 99 80", None),
    ],
)
def test_positions(fen, expected):
    assert ending(fen) == expected


def test_checkmate_beats_the_fifty_move_rule():
    assert ending("k7/1Q6/1K6/8/8/8/8/8 b - - 100 90")[1] == "checkmate"


def test_threefold_repetition():
    board = Board()
    for uci in ["g1f3", "g8f6", "f3g1", "f6g8"] * 2:
        assert position_outcome(board, 500, 0) is None
        board.make_move(board.parse_move(uci))
    assert position_outcome(board, 500, 8).termination == "threefold_repetition"


def test_max_moves_counts_full_moves():
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    assert ending(fen, max_moves=3, plies=5) is None
    assert ending(fen, max_moves=3, plies=6) == ("1/2-1/2", "max_moves", None)


def test_timeout():
    board = Board.from_fen("4k3/8/8/8/8/8/8/Q3K3 w - - 0 1")
    assert timeout_outcome(board, BLACK) == Outcome(
        "1-0", "timeout", WHITE, "Black: ran out of time"
    )
    assert timeout_outcome(board, WHITE).termination == "timeout_insufficient_material"
    assert timeout_outcome(board, WHITE).winner is None


def test_startup():
    white_failed = loss(WHITE, "crash", "exit code 1")
    black_failed = loss(BLACK, "startup_timeout", "no ready")
    assert startup_outcome({}) is None
    assert startup_outcome({WHITE: white_failed}) == white_failed
    both = startup_outcome({BLACK: black_failed, WHITE: white_failed})
    assert (both.result, both.termination, both.winner) == ("*", "startup_timeout", None)
    assert both.detail.index("White") < both.detail.index("Black")
