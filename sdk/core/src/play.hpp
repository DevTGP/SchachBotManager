// Applying a move or a null move to a position.
#pragma once

#include "move.hpp"
#include "position.hpp"

namespace sbm {

// Applies a legal move with complete flags, as produced by generate_legal_moves.
void play_move(Position& position, Move move);

// Passes the turn: clears the en passant square and advances the counters.
void play_null_move(Position& position);

} // namespace sbm
