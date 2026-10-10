#include "log_view.hpp"

#include <algorithm>
#include <cstddef>

#include <imgui.h>

#include "theme.hpp"

namespace sbm_viewer {

namespace {

// More lines make the window slow without helping anyone read them.
constexpr size_t max_lines = 2000;
constexpr float older_alpha = 0.55f;

ImVec4 level_color(LogLevel level) {
    switch (level) {
        case LogLevel::debug:
            return colors::muted;
        case LogLevel::warn:
            return colors::warn;
        case LogLevel::error:
            return colors::error;
        case LogLevel::info:
            break;
    }
    return ImGui::GetStyleColorVec4(ImGuiCol_Text);
}

const char* level_tag(LogLevel level) {
    switch (level) {
        case LogLevel::debug:
            return "debug";
        case LogLevel::warn:
            return "warn ";
        case LogLevel::error:
            return "error";
        case LogLevel::info:
            break;
    }
    return "info ";
}

} // namespace

void draw_log(const GameRecord& game, ViewState& state, float height) {
    const int count = game.ply_count();
    const bool live = state.navigation.live();
    const int shown = state.navigation.shown(count);
    const auto& logs = game.logs();

    // Lines that arrived while the shown half-move was being thought about belong to it.
    const auto visible_end =
        live ? logs.end() : std::find_if(logs.begin(), logs.end(), [&](const LogLine& line) {
            return line.ply >= std::max(shown, 1);
        });
    const size_t visible = static_cast<size_t>(visible_end - logs.begin());
    const size_t first = visible > max_lines ? visible - max_lines : 0;

    if (!ImGui::BeginChild(
            "log", ImVec2(0.0f, height), ImGuiChildFlags_Borders,
            ImGuiWindowFlags_HorizontalScrollbar)) {
        ImGui::EndChild();
        return;
    }
    if (visible == 0) {
        ImGui::TextDisabled("No log lines yet.");
    }
    for (size_t i = first; i < visible; ++i) {
        const LogLine& line = logs[i];
        const bool current = line.ply >= shown - 1;
        ImVec4 color = level_color(line.message.level);
        if (!current) {
            color.w *= older_alpha;
        }
        ImGui::PushStyleColor(ImGuiCol_Text, color);
        if (!line.message.time.empty()) {
            ImGui::TextUnformatted(line.message.time.c_str());
            ImGui::SameLine();
        }
        ImGui::TextUnformatted(level_tag(line.message.level));
        ImGui::SameLine();
        ImGui::TextUnformatted(line.message.text.c_str());
        ImGui::PopStyleColor();
    }
    if (visible != state.log_lines_shown) {
        state.log_lines_shown = visible;
        ImGui::SetScrollHereY(1.0f);
    }
    ImGui::EndChild();
}

} // namespace sbm_viewer
