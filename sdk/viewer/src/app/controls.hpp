// Stepping through the game with buttons and keys, and turning the board.
#pragma once

#include "model/game_record.hpp"
#include "view_state.hpp"

namespace sbm_viewer {

// Buttons below the board.
void draw_controls(const GameRecord& game, ViewState& state);
// Left/Right step, Home/End jump, F flips; the mouse wheel steps over `board_hovered`.
void handle_keys(const GameRecord& game, ViewState& state, bool board_hovered);

} // namespace sbm_viewer
