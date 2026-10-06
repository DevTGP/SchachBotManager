// Attacks within a position: attackers of a square, checkers and pinned pieces.
#pragma once

#include "bitboard.hpp"
#include "piece.hpp"
#include "position.hpp"

namespace sbm {

// Pieces of `by` that attack the square, with the given occupancy. Pins are ignored.
Bitboard attackers_of(const Position& position, int square, Color by, Bitboard occupied);
Bitboard attackers_of(const Position& position, int square, Color by);

bool is_attacked(const Position& position, int square, Color by);

// Squares attacked by the piece on the square, including own pieces; empty for an empty square.
Bitboard attacks_from(const Position& position, int square);

// Pieces giving check to the side to move.
Bitboard checkers(const Position& position);

// Pieces of that color pinned to their own king by an enemy bishop, rook or queen.
Bitboard pinned(const Position& position, Color color);

} // namespace sbm
