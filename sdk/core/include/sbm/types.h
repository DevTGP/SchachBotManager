/* Value types, codes (E34, E35, E45, E47) and buffer sizes of the C interface.
 * Named squares A1 to H8 and the log levels live only in spec/api/constants.json. */
#ifndef SBM_TYPES_H
#define SBM_TYPES_H

#include <stdint.h>

typedef uint16_t sbm_move;
typedef uint64_t sbm_bitboard;
typedef uint8_t sbm_color;
typedef uint8_t sbm_piece_type;
typedef uint8_t sbm_piece;
typedef uint8_t sbm_square;
typedef uint8_t sbm_castling;

/* 0 or 1. A fixed-size integer instead of bool, which foreign function interfaces marshal
 * differently (e.g. .NET treats bool as a 4-byte value by default). */
typedef int32_t sbm_bool;

enum { SBM_WHITE = 0, SBM_BLACK = 1 };

enum {
    SBM_PAWN = 0,
    SBM_KNIGHT = 1,
    SBM_BISHOP = 2,
    SBM_ROOK = 3,
    SBM_QUEEN = 4,
    SBM_KING = 5,
    SBM_NO_PIECE_TYPE = 6
};

/* Piece = color * 6 + piece type. */
enum { SBM_NO_PIECE = 12 };

enum { SBM_NO_SQUARE = 64 };

enum {
    SBM_WHITE_KINGSIDE = 1,
    SBM_WHITE_QUEENSIDE = 2,
    SBM_BLACK_KINGSIDE = 4,
    SBM_BLACK_QUEENSIDE = 8
};

/* Bits 0 to 5 from-square, 6 to 11 to-square, 12 to 15 flags. */
enum {
    SBM_FLAG_QUIET = 0,
    SBM_FLAG_DOUBLE_PAWN_PUSH = 1,
    SBM_FLAG_KING_CASTLE = 2,
    SBM_FLAG_QUEEN_CASTLE = 3,
    SBM_FLAG_CAPTURE = 4,
    SBM_FLAG_EN_PASSANT = 5,
    SBM_FLAG_PROMOTION = 8,         /* + 0 knight, 1 bishop, 2 rook, 3 queen */
    SBM_FLAG_PROMOTION_CAPTURE = 12 /* same order */
};

#define SBM_NULL_MOVE ((sbm_move)0)
#define SBM_RESIGN ((sbm_move)0xFFFF)

/* Element counts of fixed-size output arrays. */
enum {
    SBM_MAX_MOVES = 256, /* more than the 218 legal moves of any position */
    SBM_PIECE_COUNT = 12,
    SBM_SQUARE_COUNT = 64
};

/* Buffer sizes for text output, including the terminating NUL. */
enum {
    SBM_FEN_BUFFER_SIZE = 128, /* a FEN has at most 103 characters */
    SBM_UCI_BUFFER_SIZE = 6,
    SBM_SAN_BUFFER_SIZE = 16,
    SBM_TEXT_BUFFER_SIZE = 512
};

#endif
