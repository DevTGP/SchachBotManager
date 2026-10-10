// The moves of the game in a table; a click shows the position after that move.
#pragma once

#include "model/game_record.hpp"
#include "view_state.hpp"

namespace sbm_viewer {

void draw_move_list(const GameRecord& game, ViewState& state, float height);

} // namespace sbm_viewer
