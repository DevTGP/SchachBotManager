// Legal and pseudo-legal move generation with complete move values (E34, E188).
#pragma once

#include <optional>

#include "move.hpp"
#include "move_list.hpp"
#include "position.hpp"

namespace sbm {

void generate_legal_moves(const Position& position, MoveList& list);

// Legal captures including en passant and promotions with capture.
void generate_legal_captures(const Position& position, MoveList& list);

// The legal move matching the value on from-square, to-square and promotion piece; nothing for
// values with flags 6 or 7 and for moves that are not legal.
std::optional<Move> find_legal_move(const Position& position, Move move);

// Moves of the piece on the square by its movement rules, as if its color were to move: pins,
// checks and the own king are ignored, castling only where it is legal for that color, en passant
// only for the side to move (E188). Nothing for an empty square.
void generate_moves_from(const Position& position, int from, MoveList& list);

} // namespace sbm
