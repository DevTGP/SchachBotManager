"""Python behaviour of Board.pieces and PlacedPiece beyond the vectors (E190)."""

import pytest

import sbm

KINGS = "8/8/8/8/8/8/8/K6k w - - 0 1"


def test_filters_default_to_all_pieces():
    board = sbm.Board()
    assert len(board.pieces()) == 32
    assert board.pieces() == board.pieces(sbm.NO_COLOR, sbm.NO_PIECE_TYPE)
    assert board.pieces(piece_type=sbm.KING) == board.pieces(None, sbm.KING)
    assert [p.square for p in board.pieces(sbm.WHITE, sbm.KNIGHT)] == [sbm.B1, sbm.G1]


def test_placed_piece_unpacks_and_compares():
    board = sbm.Board.from_fen(KINGS)
    white, black = board.pieces()
    square, piece = white
    assert (square, piece) == (sbm.A1, sbm.WHITE_KING)
    assert (black.square, black.piece) == (sbm.H1, sbm.BLACK_KING)
    assert white == sbm.Board.from_fen(KINGS).pieces()[0]
    assert white != black
    assert len({white, sbm.Board.from_fen(KINGS).pieces()[0]}) == 1
    assert repr(white) == "PlacedPiece(square=0, piece=5)"


def test_placed_piece_is_read_only():
    (first, _) = sbm.Board.from_fen(KINGS).pieces()
    with pytest.raises(AttributeError):
        first.square = 5


def test_invalid_filters_raise():
    board = sbm.Board()
    with pytest.raises(sbm.InvalidArgumentError):
        board.pieces(3)
    with pytest.raises(sbm.InvalidArgumentError):
        board.pieces(piece_type=7)


def test_legal_moves_of_one_piece_come_from_legal_moves():
    board = sbm.Board.from_fen("4k3/4r3/8/8/8/8/4B3/4K3 w - - 0 1")
    assert board.all_moves_from(sbm.E2)
    assert [m for m in board.legal_moves() if m.from_square() == sbm.E2] == []
