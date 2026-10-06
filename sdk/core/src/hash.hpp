// Board.hash: the Polyglot key of a position (E46).
#pragma once

#include <cstdint>

#include "position.hpp"

namespace sbm {

// The en passant file counts if a pawn of the side to move stands next to the pushed pawn,
// without checking legality.
std::uint64_t polyglot_hash(const Position& position);

} // namespace sbm
