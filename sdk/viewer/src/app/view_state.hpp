// What the user chose in the window and what the loop knows about the input.
#pragma once

#include <cstddef>
#include <cstdint>

#include "model/navigation.hpp"

namespace sbm_viewer {

struct ViewState {
    Navigation navigation;
    // Turns the board around; by default the bot's side is at the bottom.
    bool flipped = false;
    // SDL ticks when the newest game last changed; the running clock counts down from there.
    uint64_t changed_at_ms = 0;
    // The bot program has ended.
    bool input_closed = false;
    // Log lines shown in the last frame; more of them scroll the log down.
    size_t log_lines_shown = 0;
};

} // namespace sbm_viewer
