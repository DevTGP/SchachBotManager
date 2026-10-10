// A bar above or below the board: color, name and clock of one side.
#pragma once

#include <cstdint>
#include <optional>
#include <string>

namespace sbm_viewer {

struct PlayerBar {
    std::string name;
    bool is_bot = false;
    bool white = true;
    std::optional<int64_t> clock_ms;
    bool to_move = false;
    // The clock counts down right now (live view of a running game).
    bool running = false;
};

void draw_player_bar(const PlayerBar& bar, float width);
// Height the bar takes, for the layout.
float player_bar_height();

} // namespace sbm_viewer
