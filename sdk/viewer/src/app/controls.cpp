#include "controls.hpp"

#include <imgui.h>

#include "theme.hpp"

namespace sbm_viewer {

void draw_controls(const GameRecord& game, ViewState& state) {
    Navigation& navigation = state.navigation;
    const int count = game.ply_count();
    const int shown = navigation.shown(count);

    ImGui::BeginDisabled(shown == 0);
    if (ImGui::Button("⇤")) {
        navigation.first(count);
    }
    ImGui::SetItemTooltip("Start position (Home)");
    ImGui::SameLine();
    if (ImGui::Button("◀")) {
        navigation.step(-1, count);
    }
    ImGui::SetItemTooltip("Previous move (Left)");
    ImGui::EndDisabled();
    ImGui::SameLine();
    ImGui::BeginDisabled(navigation.live());
    if (ImGui::Button("▶")) {
        navigation.step(1, count);
    }
    ImGui::SetItemTooltip("Next move (Right)");
    ImGui::SameLine();
    if (ImGui::Button("⇥")) {
        navigation.last();
    }
    ImGui::SetItemTooltip("Latest move, follow the game live (End)");
    ImGui::EndDisabled();

    ImGui::SameLine();
    if (navigation.live()) {
        ImGui::TextColored(colors::active_clock, "● Live");
    } else {
        ImGui::Text("Move %d of %d", shown, count);
    }
    ImGui::SameLine();
    if (ImGui::Button("Flip")) {
        state.flipped = !state.flipped;
    }
    ImGui::SetItemTooltip("Turn the board around (F)");
}

void handle_keys(const GameRecord& game, ViewState& state, bool board_hovered) {
    const ImGuiIO& io = ImGui::GetIO();
    Navigation& navigation = state.navigation;
    const int count = game.ply_count();
    if (!io.WantTextInput) {
        if (ImGui::IsKeyPressed(ImGuiKey_LeftArrow)) {
            navigation.step(-1, count);
        }
        if (ImGui::IsKeyPressed(ImGuiKey_RightArrow)) {
            navigation.step(1, count);
        }
        if (ImGui::IsKeyPressed(ImGuiKey_Home, false)) {
            navigation.first(count);
        }
        if (ImGui::IsKeyPressed(ImGuiKey_End, false)) {
            navigation.last();
        }
        if (ImGui::IsKeyPressed(ImGuiKey_F, false)) {
            state.flipped = !state.flipped;
        }
    }
    if (board_hovered && io.MouseWheel != 0.0f) {
        navigation.step(io.MouseWheel > 0.0f ? -1 : 1, count);
    }
}

} // namespace sbm_viewer
