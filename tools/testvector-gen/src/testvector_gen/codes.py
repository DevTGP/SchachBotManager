"""Conversion between python-chess and the codes of E34 (moves) and E35 (pieces, colors)."""

import chess

WHITE = 0
BLACK = 1
PIECE_TYPES = 6
NO_PIECE_TYPE = 6
NO_PIECE = 12
SQUARES = 64
NO_SQUARE = 64

NULL_MOVE = 0
RESIGN = 0xFFFF
QUIET = 0
DOUBLE_PUSH = 1
KING_CASTLE = 2
QUEEN_CASTLE = 3
CAPTURE = 4
EN_PASSANT = 5
UNUSED_FLAGS = (6, 7)
PROMOTION = 8
PROMOTION_CAPTURE = 12
MAX_FLAGS = 15
PROMOTION_LETTERS = "nbrq"

CASTLING_BITS = (
    (1, chess.WHITE, chess.BB_H1),
    (2, chess.WHITE, chess.BB_A1),
    (4, chess.BLACK, chess.BB_H8),
    (8, chess.BLACK, chess.BB_A8),
)


def color_code(color: chess.Color) -> int:
    return WHITE if color == chess.WHITE else BLACK


def chess_color(code: int) -> chess.Color:
    return chess.WHITE if code == WHITE else chess.BLACK


def chess_piece_type(code: int) -> chess.PieceType:
    return code + 1


def piece_code(piece: chess.Piece | None) -> int:
    if piece is None:
        return NO_PIECE
    return color_code(piece.color) * PIECE_TYPES + piece.piece_type - 1


def castling_code(board: chess.Board) -> int:
    return sum(bit for bit, _, rook in CASTLING_BITS if board.castling_rights & rook)


def move_value(from_square: int, to_square: int, flags: int) -> int:
    return from_square | to_square << 6 | flags << 12


def move_parts(value: int) -> tuple[int, int, int]:
    """From-square, to-square and flags of a move value."""
    return value & 63, value >> 6 & 63, value >> 12


def promotion_type(flags: int) -> chess.PieceType | None:
    """python-chess piece type of a promotion, None for other flags."""
    return (flags & 3) + chess.KNIGHT if flags >= PROMOTION else None


def encode_move(board: chess.Board, move: chess.Move) -> int:
    """Complete move value with all flags; `move` must be legal on `board` or the null move."""
    if move == chess.Move.null():
        return NULL_MOVE
    capture = board.is_capture(move)
    if move.promotion is not None:
        base = PROMOTION_CAPTURE if capture else PROMOTION
        flags = base + move.promotion - chess.KNIGHT
    elif board.is_castling(move):
        kingside = chess.square_file(move.to_square) > chess.square_file(move.from_square)
        flags = KING_CASTLE if kingside else QUEEN_CASTLE
    elif board.is_en_passant(move):
        flags = EN_PASSANT
    elif capture:
        flags = CAPTURE
    elif board.piece_type_at(move.from_square) == chess.PAWN and (
        abs(move.to_square - move.from_square) == 16
    ):
        flags = DOUBLE_PUSH
    else:
        flags = QUIET
    return move_value(move.from_square, move.to_square, flags)
