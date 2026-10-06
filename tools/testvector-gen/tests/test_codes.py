import chess
import pytest

from testvector_gen.codes import (
    NO_PIECE,
    castling_code,
    encode_move,
    move_parts,
    move_value,
    piece_code,
)

KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
PROMOTION = "1n2k3/P7/8/8/8/8/8/4K3 w - - 0 1"


def test_move_value_round_trip():
    value = move_value(chess.E2, chess.E4, 1)
    assert value == 5900
    assert move_parts(value) == (chess.E2, chess.E4, 1)


@pytest.mark.parametrize(
    ("piece", "code"),
    [
        (chess.Piece(chess.PAWN, chess.WHITE), 0),
        (chess.Piece(chess.KING, chess.WHITE), 5),
        (chess.Piece(chess.PAWN, chess.BLACK), 6),
        (chess.Piece(chess.KING, chess.BLACK), 11),
        (None, NO_PIECE),
    ],
)
def test_piece_code(piece, code):
    assert piece_code(piece) == code


def test_castling_code():
    assert castling_code(chess.Board()) == 15
    assert castling_code(chess.Board("r3k2r/8/8/8/8/8/8/R3K2R w Kq - 0 1")) == 9


@pytest.mark.parametrize(
    ("fen", "uci", "flags"),
    [
        (chess.STARTING_FEN, "g1f3", 0),
        (chess.STARTING_FEN, "e2e4", 1),
        (KIWIPETE, "e1g1", 2),
        (KIWIPETE, "e1c1", 3),
        (KIWIPETE, "e5f7", 4),
        ("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1", "e5d6", 5),
        (PROMOTION, "a7a8n", 8),
        (PROMOTION, "a7a8q", 11),
        (PROMOTION, "a7b8n", 12),
        (PROMOTION, "a7b8q", 15),
    ],
)
def test_encode_move_flags(fen, uci, flags):
    board = chess.Board(fen)
    move = chess.Move.from_uci(uci)
    assert move_parts(encode_move(board, move)) == (move.from_square, move.to_square, flags)


def test_encode_null_move():
    assert encode_move(chess.Board(), chess.Move.null()) == 0
