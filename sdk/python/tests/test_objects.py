"""Python behaviour of Move and Board beyond the vectors: equality, copies and memory."""

import copy
import gc
import subprocess
import sys
import weakref

import pytest

import sbm

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def test_move_value_semantics():
    move = sbm.Move(sbm.E2, sbm.E4, sbm.DOUBLE_PAWN_PUSH)
    assert move == sbm.Move.from_value(move.value())
    assert move != sbm.Move.parse("e2e4")
    assert move != move.value()
    assert len({move, sbm.Move.from_value(move.value())}) == 1
    assert copy.copy(move) is move
    assert copy.deepcopy(move) is move
    assert repr(move) == "<Move e2e4 flags=1>"
    assert repr(sbm.NULL_MOVE) == "<Move NULL_MOVE>"
    assert repr(sbm.RESIGN) == "<Move RESIGN>"


def test_move_is_immutable():
    move = sbm.Move.parse("e2e4")
    with pytest.raises(AttributeError):
        move.value = 5
    assert move.value() == 1804


def test_board_copies_are_independent():
    board = sbm.Board()
    board.make_move(board.parse_move("e2e4"))
    for duplicate in [board.copy(), copy.copy(board), copy.deepcopy(board)]:
        assert duplicate is not board
        duplicate.undo_move()
        assert duplicate.fen() == START
        assert duplicate.move_history() == []
    assert board.move_history() == [board.copy().move_history()[0]]
    assert board.fen() != START


def test_board_text_forms():
    board = sbm.Board()
    assert repr(board) == f"Board.from_fen('{START}')"
    assert str(board) == board.to_text()


def test_board_is_freed():
    board = sbm.Board()
    reference = weakref.ref(board)
    del board
    gc.collect()
    assert reference() is None


def test_many_copies():
    board = sbm.Board.from_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    for _ in range(100_000):
        duplicate = board.copy()
        duplicate.make_move(duplicate.legal_moves()[0])
    assert board.move_history() == []


def test_no_leaks_at_exit():
    # nanobind reports objects that outlive the interpreter on stderr.
    script = "; ".join(
        [
            "import sbm",
            "board = sbm.Board()",
            "moves = board.legal_moves()",
            "special = (sbm.NULL_MOVE, sbm.Move.RESIGN)",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True
    )
    assert "leaked" not in result.stderr
