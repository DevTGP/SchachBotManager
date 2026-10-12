// Range checks of square, color and piece type arguments; violations give SBM_INVALID_ARGUMENT.
#pragma once

#include "bitboard.hpp"
#include "piece.hpp"
#include "sbm/types.h"

namespace sbm::capi {

constexpr bool valid_square(sbm_square square) {
    return square < kSquareCount;
}

constexpr bool valid_color(sbm_color color) {
    return color < kColorCount;
}

constexpr bool valid_piece_type(sbm_piece_type piece_type) {
    return piece_type < kPieceTypeCount;
}

// Filters additionally accept SBM_NO_COLOR and SBM_NO_PIECE_TYPE for "any" (E190).
constexpr bool valid_color_filter(sbm_color color) {
    return color <= kColorCount;
}

constexpr bool valid_piece_type_filter(sbm_piece_type piece_type) {
    return piece_type <= kPieceTypeCount;
}

} // namespace sbm::capi
