// The bot's log lines up to the shown half-move; lines of that half-move stand out.
#pragma once

#include "model/game_record.hpp"
#include "view_state.hpp"

namespace sbm_viewer {

void draw_log(const GameRecord& game, ViewState& state, float height);

} // namespace sbm_viewer
