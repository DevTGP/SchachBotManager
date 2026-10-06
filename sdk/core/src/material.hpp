// Board.has_insufficient_material, with the rules of python-chess.
#pragma once

#include "position.hpp"

namespace sbm {

// That color cannot checkmate: only its king, or king and one knight against nothing but king
// and queens, or only bishops all standing on one square color with no pawns or knights on the
// board.
bool has_insufficient_material(const Position& position, Color color);

} // namespace sbm
