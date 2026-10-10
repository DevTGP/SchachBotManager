// The board of the shown position with the last move, a check and coordinates.
#pragma once

#include "model/game_record.hpp"

struct ImFont;

namespace sbm_viewer {

// Draws at the cursor in a square of `size` and takes that space.
void draw_board(const GameRecord& game, int shown, bool white_bottom, ImFont* font, float size);

} // namespace sbm_viewer
