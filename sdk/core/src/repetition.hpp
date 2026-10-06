// Board.is_repetition.
#pragma once

#include "game.hpp"

namespace sbm {

// How often the current position occurs in the game, counting itself. Positions are equal if
// pieces, side to move, castling rights and the en passant square as in the FEN are equal.
int repetition_count(const Game& game);

} // namespace sbm
