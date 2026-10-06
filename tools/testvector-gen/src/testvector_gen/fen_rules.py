"""Board.from_fen with exactly the syntax and position rules of spec/api/board.json."""

import re

import chess

from testvector_gen.errors import INVALID_FEN, ApiError

I32_MAX = 2**31 - 1
MAX_PIECES = 16
RANKS = 8
RANK = re.compile(r"[PNBRQKpnbrqk1-8]+")
ADJACENT_DIGITS = re.compile(r"[1-8]{2}")
SIDE = re.compile(r"[wb]")
CASTLING = re.compile(r"-|KQ?k?q?|Qk?q?|kq?|q")
EN_PASSANT = re.compile(r"-|[a-h][36]")
HALFMOVE = re.compile(r"0|[1-9][0-9]*")
FULLMOVE = re.compile(r"[1-9][0-9]*")

# Castling letter, then king and rook that must stand on their start squares.
CASTLING_PIECES = {
    "K": (chess.E1, chess.H1, chess.WHITE),
    "Q": (chess.E1, chess.A1, chess.WHITE),
    "k": (chess.E8, chess.H8, chess.BLACK),
    "q": (chess.E8, chess.A8, chess.BLACK),
}


def parse_fen(text: str) -> chess.Board:
    """Returns the board, keeping the en passant square as given; raises InvalidFen."""
    fields = text.split(" ")
    if len(fields) != 6 or not _valid_syntax(*fields):
        raise ApiError(INVALID_FEN)
    placement, _, castling, en_passant, _, _ = fields
    board = chess.Board(text)
    if not _valid_position(board, castling, en_passant):
        raise ApiError(INVALID_FEN)
    if board.fen(en_passant="fen") != text:
        raise AssertionError(f"python-chess read the FEN differently: {text}")
    return board


def _valid_syntax(
    placement: str, side: str, castling: str, en_passant: str, halfmove: str, fullmove: str
) -> bool:
    ranks = placement.split("/")
    return (
        len(ranks) == RANKS
        and all(_valid_rank(rank) for rank in ranks)
        and SIDE.fullmatch(side) is not None
        and CASTLING.fullmatch(castling) is not None
        and EN_PASSANT.fullmatch(en_passant) is not None
        and HALFMOVE.fullmatch(halfmove) is not None
        and FULLMOVE.fullmatch(fullmove) is not None
        and int(halfmove) <= I32_MAX
        and int(fullmove) <= I32_MAX
    )


def _valid_rank(rank: str) -> bool:
    if RANK.fullmatch(rank) is None or ADJACENT_DIGITS.search(rank):
        return False
    return sum(int(char) if char.isdigit() else 1 for char in rank) == RANKS


def _valid_position(board: chess.Board, castling: str, en_passant: str) -> bool:
    for color in chess.COLORS:
        if len(board.pieces(chess.KING, color)) != 1:
            return False
        if chess.popcount(board.occupied_co[color]) > MAX_PIECES:
            return False
    if board.pawns & (chess.BB_RANK_1 | chess.BB_RANK_8):
        return False
    if board.is_attacked_by(board.turn, board.king(not board.turn)):
        return False
    if castling != "-" and not all(_has_castling_pieces(board, flag) for flag in castling):
        return False
    return en_passant == "-" or _valid_en_passant(board, chess.parse_square(en_passant))


def _has_castling_pieces(board: chess.Board, flag: str) -> bool:
    king, rook, color = CASTLING_PIECES[flag]
    return board.piece_at(king) == chess.Piece(chess.KING, color) and board.piece_at(
        rook
    ) == chess.Piece(chess.ROOK, color)


def _valid_en_passant(board: chess.Board, square: chess.Square) -> bool:
    """The square a pawn of the side not to move just passed with a double push."""
    forward = 8 if board.turn == chess.WHITE else -8
    target_rank = 5 if board.turn == chess.WHITE else 2
    pawn = chess.Piece(chess.PAWN, not board.turn)
    return (
        chess.square_rank(square) == target_rank
        and board.piece_at(square) is None
        and board.piece_at(square + forward) is None
        and board.piece_at(square - forward) == pawn
    )
