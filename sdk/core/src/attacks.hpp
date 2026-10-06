// Attack sets of single pieces on an empty or given occupancy, and lines between squares.
#pragma once

#include "bitboard.hpp"
#include "piece.hpp"

namespace sbm {

Bitboard pawn_attacks(Color color, int square);
Bitboard knight_attacks(int square);
Bitboard king_attacks(int square);
Bitboard bishop_attacks(int square, Bitboard occupied);
Bitboard rook_attacks(int square, Bitboard occupied);
Bitboard queen_attacks(int square, Bitboard occupied);

// Squares attacked by a piece of that type and color; pawns attack diagonally only.
Bitboard piece_attacks(PieceType type, Color color, int square, Bitboard occupied);

// Squares strictly between two squares on a common rank, file or diagonal; empty otherwise.
Bitboard between(int a, int b);

// The whole rank, file or diagonal through both squares; empty if they share none.
Bitboard line_through(int a, int b);

} // namespace sbm
