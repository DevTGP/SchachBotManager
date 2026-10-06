"""Named constants of the bot API (spec/api/constants.json) as plain integers."""

from sbm._core import Move

# Color
WHITE, BLACK = 0, 1

# PieceType
PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING, NO_PIECE_TYPE = range(7)

# Piece: color * 6 + piece type
WHITE_PAWN, WHITE_KNIGHT, WHITE_BISHOP, WHITE_ROOK, WHITE_QUEEN, WHITE_KING = range(0, 6)
BLACK_PAWN, BLACK_KNIGHT, BLACK_BISHOP, BLACK_ROOK, BLACK_QUEEN, BLACK_KING = range(6, 12)
NO_PIECE = 12

# Square: rank * 8 + file
A1, B1, C1, D1, E1, F1, G1, H1 = range(0, 8)
A2, B2, C2, D2, E2, F2, G2, H2 = range(8, 16)
A3, B3, C3, D3, E3, F3, G3, H3 = range(16, 24)
A4, B4, C4, D4, E4, F4, G4, H4 = range(24, 32)
A5, B5, C5, D5, E5, F5, G5, H5 = range(32, 40)
A6, B6, C6, D6, E6, F6, G6, H6 = range(40, 48)
A7, B7, C7, D7, E7, F7, G7, H7 = range(48, 56)
A8, B8, C8, D8, E8, F8, G8, H8 = range(56, 64)
NO_SQUARE = 64

# CastlingRights: bit mask
NO_CASTLING = 0
WHITE_KINGSIDE = 1
WHITE_QUEENSIDE = 2
BLACK_KINGSIDE = 4
BLACK_QUEENSIDE = 8
ALL_CASTLING = 15

# MoveFlags
QUIET = 0
DOUBLE_PAWN_PUSH = 1
KING_CASTLE = 2
QUEEN_CASTLE = 3
CAPTURE = 4
EN_PASSANT = 5
PROMOTION_KNIGHT, PROMOTION_BISHOP, PROMOTION_ROOK, PROMOTION_QUEEN = range(8, 12)
PROMOTION_CAPTURE_KNIGHT, PROMOTION_CAPTURE_BISHOP = 12, 13
PROMOTION_CAPTURE_ROOK, PROMOTION_CAPTURE_QUEEN = 14, 15

# Move
NULL_MOVE = Move.NULL_MOVE
RESIGN = Move.RESIGN

# LogLevel
TRACE, DEBUG, INFO, WARN, ERROR, OFF = range(6)

__all__ = [name for name in dir() if name.isupper()]
