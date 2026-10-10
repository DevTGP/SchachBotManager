// Details of the shown half-move: who played it, thinking time and the bot's search info.
#pragma once

#include "model/game_record.hpp"

namespace sbm_viewer {

void draw_details(const GameRecord& game, int shown);

} // namespace sbm_viewer
