"""Errors as Python exceptions and arguments that do not fit the C types (E49)."""

import pytest

import sbm

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def test_hierarchy():
    for name in [
        "InvalidArgumentError",
        "InvalidFenError",
        "InvalidUciError",
        "IllegalMoveError",
        "InvalidStateError",
        "DataNotFoundError",
    ]:
        assert issubclass(getattr(sbm, name), sbm.ChessError)
    assert issubclass(sbm.ChessError, Exception)


@pytest.mark.parametrize("value", [-1, 256, 2**64, -(2**70)])
def test_integers_outside_the_c_type(value):
    board = sbm.Board()
    with pytest.raises(sbm.InvalidArgumentError):
        board.piece_at(value)
    with pytest.raises(sbm.InvalidArgumentError):
        board.attackers_of(sbm.E4, value)
    with pytest.raises(sbm.InvalidArgumentError):
        sbm.Move(value, sbm.E4, sbm.QUIET)
    with pytest.raises(sbm.InvalidArgumentError):
        sbm.Move.from_value(value * 1000)


def test_repetition_count_outside_i32():
    with pytest.raises(sbm.InvalidArgumentError):
        sbm.Board().is_repetition(2**31)


def test_wrong_types():
    board = sbm.Board()
    with pytest.raises(TypeError):
        board.piece_at("e4")
    with pytest.raises(TypeError):
        board.make_move(1804)
    with pytest.raises(TypeError):
        sbm.Board.from_fen(None)


def test_embedded_nul():
    with pytest.raises(sbm.InvalidFenError):
        sbm.Board.from_fen(START + "\0x")
    with pytest.raises(sbm.InvalidUciError):
        sbm.Move.parse("e2e4\0")
    with pytest.raises(sbm.InvalidUciError):
        sbm.Board().parse_move("e2e4\0")


def test_message_names_the_call_and_move():
    board = sbm.Board()
    with pytest.raises(sbm.IllegalMoveError, match=r"Board\.make_move\(<Move e2e5 flags=0>\)"):
        board.make_move(sbm.Move.parse("e2e5"))
    assert board.fen() == START


def test_unused_flags_rejected():
    with pytest.raises(sbm.InvalidArgumentError):
        sbm.Move(sbm.E2, sbm.E4, 6)
    with pytest.raises(sbm.InvalidArgumentError):
        sbm.Move(sbm.E2, sbm.E4, 16)
