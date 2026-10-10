#include "players_view.hpp"

#include <imgui.h>

#include "model/time_text.hpp"
#include "theme.hpp"

namespace sbm_viewer {

namespace {

constexpr float clock_scale = 1.5f;

} // namespace

float player_bar_height() {
    return ImGui::GetFontSize() * clock_scale + ImGui::GetStyle().ItemSpacing.y;
}

void draw_player_bar(const PlayerBar& bar, float width) {
    const float start_x = ImGui::GetCursorPosX();
    ImGui::PushFont(nullptr, ImGui::GetStyle().FontSizeBase * clock_scale);
    ImGui::TextUnformatted(bar.white ? "♔" : "♚");
    ImGui::SameLine();
    ImGui::TextUnformatted(bar.name.c_str());
    if (bar.is_bot) {
        ImGui::SameLine();
        ImGui::TextDisabled("(bot)");
    }
    if (bar.clock_ms) {
        const std::string clock = clock_text(*bar.clock_ms);
        ImGui::SameLine(start_x + width - ImGui::CalcTextSize(clock.c_str()).x);
        const ImVec4 color = bar.running   ? colors::active_clock
                             : bar.to_move ? ImGui::GetStyleColorVec4(ImGuiCol_Text)
                                           : colors::muted;
        ImGui::TextColored(color, "%s", clock.c_str());
    }
    ImGui::PopFont();
}

} // namespace sbm_viewer
