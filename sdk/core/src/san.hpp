// Standard algebraic notation (Board.san).
#pragma once

#include <string>

#include "move.hpp"
#include "position.hpp"

namespace sbm {

// SAN of a legal move with complete flags, including + for check and # for mate. Ambiguous
// piece moves add the from-file, the from-rank or both, in the manner of python-chess.
std::string write_san(const Position& position, Move move);

} // namespace sbm
