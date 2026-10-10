// One frame of the window: board with players and controls on the left, game details on the right.
#pragma once

#include <cstdint>

#include "model/session.hpp"
#include "view_state.hpp"

struct ImFont;

namespace sbm_viewer {

void draw_frame(const Session& session, ViewState& state, ImFont* font, uint64_t now_ms);

} // namespace sbm_viewer
