#include "material.hpp"

namespace sbm {

namespace {

Bitboard all_of(const Position& position, PieceType type) {
    return position.pieces_of(kWhite, type) | position.pieces_of(kBlack, type);
}

} // namespace

bool has_insufficient_material(const Position& position, Color color) {
    const Bitboard own = position.colors[color];
    if ((own & (all_of(position, kPawn) | all_of(position, kRook) | all_of(position, kQueen))) !=
        0) {
        return false;
    }
    if (position.pieces_of(color, kKnight) != 0) {
        const Bitboard others =
            position.colors[opposite(color)] & ~all_of(position, kKing) & ~all_of(position, kQueen);
        return popcount(own) <= 2 && others == 0;
    }
    if (position.pieces_of(color, kBishop) != 0) {
        const Bitboard bishops = all_of(position, kBishop);
        const bool one_color = (bishops & kDarkSquares) == 0 || (bishops & kLightSquares) == 0;
        return one_color && all_of(position, kPawn) == 0 && all_of(position, kKnight) == 0;
    }
    return true;
}

} // namespace sbm
