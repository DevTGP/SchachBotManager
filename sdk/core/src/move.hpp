// Move values of E34: bits 0 to 5 from-square, 6 to 11 to-square, 12 to 15 flags.
#pragma once

#include <cstdint>

#include "piece.hpp"

namespace sbm {

using Move = std::uint16_t;

enum MoveFlag : int {
    kQuiet = 0,
    kDoublePawnPush = 1,
    kKingCastle = 2,
    kQueenCastle = 3,
    kCapture = 4,
    kEnPassant = 5,
    kPromotion = 8,         // + 0 knight, 1 bishop, 2 rook, 3 queen
    kPromotionCapture = 12, // same order
};

inline constexpr Move kNullMove = 0;
inline constexpr Move kResign = 0xFFFF;

constexpr Move encode_move(int from, int to, int flags) {
    return static_cast<Move>(from | to << 6 | flags << 12);
}

constexpr int from_square(Move move) {
    return move & 63;
}

constexpr int to_square(Move move) {
    return move >> 6 & 63;
}

constexpr int move_flags(Move move) {
    return move >> 12;
}

// Flags 6 and 7 are unused; no move carries them.
constexpr bool has_valid_flags(Move move) {
    return move_flags(move) != 6 && move_flags(move) != 7;
}

constexpr bool is_promotion(Move move) {
    return move_flags(move) >= kPromotion;
}

constexpr PieceType promotion_type(Move move) {
    return is_promotion(move) ? static_cast<PieceType>((move_flags(move) & 3) + kKnight)
                              : kNoPieceType;
}

constexpr bool is_capture(Move move) {
    const int flags = move_flags(move);
    return flags == kCapture || flags == kEnPassant || flags >= kPromotionCapture;
}

constexpr bool is_castling(Move move) {
    return move_flags(move) == kKingCastle || move_flags(move) == kQueenCastle;
}

// Moves match on from-square, to-square and promotion piece (spec/api/board_moves.json).
constexpr bool same_move(Move a, Move b) {
    return from_square(a) == from_square(b) && to_square(a) == to_square(b) &&
           promotion_type(a) == promotion_type(b);
}

} // namespace sbm
