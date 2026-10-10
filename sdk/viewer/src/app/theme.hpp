// Colors and sizes of the window.
#pragma once

#include <imgui.h>

namespace sbm_viewer {

namespace colors {
inline constexpr ImU32 light_square = IM_COL32(240, 217, 181, 255);
inline constexpr ImU32 dark_square = IM_COL32(181, 136, 99, 255);
inline constexpr ImU32 last_move = IM_COL32(205, 210, 106, 150);
inline constexpr ImU32 check = IM_COL32(220, 60, 60, 170);
inline constexpr ImU32 white_piece = IM_COL32(255, 255, 255, 255);
inline constexpr ImU32 black_piece = IM_COL32(20, 20, 20, 255);
inline constexpr ImVec4 warn{0.95f, 0.80f, 0.30f, 1.0f};
inline constexpr ImVec4 error{0.95f, 0.40f, 0.40f, 1.0f};
inline constexpr ImVec4 muted{0.60f, 0.60f, 0.60f, 1.0f};
inline constexpr ImVec4 active_clock{0.40f, 0.85f, 0.45f, 1.0f};
} // namespace colors

// Dark style scaled for the display.
void apply_theme(float scale);

} // namespace sbm_viewer
