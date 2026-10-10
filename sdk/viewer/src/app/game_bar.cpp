#include "game_bar.hpp"

#include <string>

#include <imgui.h>

#include "theme.hpp"

namespace sbm_viewer {

namespace {

std::string game_label(const std::vector<GameRecord>& games, int index) {
    const StartMessage& start = games[static_cast<size_t>(index)].start();
    const bool bot_white = start.color == "white";
    const std::string& white = bot_white ? start.bot : start.opponent;
    const std::string& black = bot_white ? start.opponent : start.bot;
    return "Game " + std::to_string(index + 1) + ": " + white + " vs " + black;
}

void draw_choice(const std::vector<GameRecord>& games, ViewState& state) {
    const int count = static_cast<int>(games.size());
    const int current = state.navigation.game();
    ImGui::SetNextItemWidth(-1.0f);
    if (!ImGui::BeginCombo("##game", game_label(games, current).c_str())) {
        return;
    }
    for (int i = 0; i < count; ++i) {
        const bool selected = i == current;
        if (ImGui::Selectable(game_label(games, i).c_str(), selected)) {
            state.navigation.select_game(i, count);
        }
        if (selected) {
            ImGui::SetItemDefaultFocus();
        }
    }
    ImGui::EndCombo();
}

} // namespace

void draw_game_bar(const std::vector<GameRecord>& games, ViewState& state) {
    if (games.size() > 1) {
        draw_choice(games, state);
    }
    const bool newest = state.navigation.game() == static_cast<int>(games.size()) - 1;
    const GameRecord& game = games[static_cast<size_t>(state.navigation.game())];
    if (!game.start().discipline.empty()) {
        ImGui::TextDisabled("%s", game.start().discipline.c_str());
        ImGui::SameLine();
    }
    if (const auto& result = game.result()) {
        if (result->termination.empty()) {
            ImGui::Text("Result %s", result->result.c_str());
        } else {
            ImGui::Text("Result %s (%s)", result->result.c_str(), result->termination.c_str());
        }
    } else if (!newest) {
        ImGui::TextColored(colors::warn, "Game ended without a result");
    } else if (state.input_closed) {
        ImGui::TextColored(colors::warn, "The bot program has ended");
    } else {
        ImGui::TextColored(colors::active_clock, "Game running");
    }
}

} // namespace sbm_viewer
