// Choice of the game when the bot played several, and the state of the shown game.
#pragma once

#include <vector>

#include "model/game_record.hpp"
#include "view_state.hpp"

namespace sbm_viewer {

void draw_game_bar(const std::vector<GameRecord>& games, ViewState& state);

} // namespace sbm_viewer
