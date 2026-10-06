// Legal move generation with complete move values (E34).
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

} // namespace sbm
