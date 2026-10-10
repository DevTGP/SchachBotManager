#include "move_list.hpp"

#include <imgui.h>

#include "model/notation.hpp"

namespace sbm_viewer {

namespace {

void move_cell(const GameRecord& game, ViewState& state, int ply, int shown) {
    if (ply == 0) {
        return;
    }
    const PlyRecord& record = game.ply(ply);
    ImGui::PushID(ply);
    const bool selected = ply == shown;
    if (ImGui::Selectable(record.san.c_str(), selected)) {
        state.navigation.go_to(ply, game.ply_count());
    }
    if (selected && !ImGui::IsItemVisible()) {
        ImGui::SetScrollHereY(0.5f);
    }
    ImGui::PopID();
}

} // namespace

void draw_move_list(const GameRecord& game, ViewState& state, float height) {
    const Position& start = game.position(0);
    const int count = game.ply_count();
    const int shown = state.navigation.shown(count);
    const auto rows = move_rows(count, start.fullmove_number(), start.side_to_move() == SBM_BLACK);
    const ImGuiTableFlags flags = ImGuiTableFlags_RowBg | ImGuiTableFlags_ScrollY |
                                  ImGuiTableFlags_BordersOuter | ImGuiTableFlags_BordersInnerV;
    if (!ImGui::BeginTable("moves", 3, flags, ImVec2(0.0f, height))) {
        return;
    }
    ImGui::TableSetupScrollFreeze(0, 1);
    ImGui::TableSetupColumn("#", ImGuiTableColumnFlags_WidthFixed, ImGui::GetFontSize() * 2.5f);
    ImGui::TableSetupColumn("White");
    ImGui::TableSetupColumn("Black");
    ImGui::TableHeadersRow();
    for (const MoveRow& row : rows) {
        ImGui::TableNextRow();
        ImGui::TableNextColumn();
        ImGui::TextDisabled("%d.", row.number);
        ImGui::TableNextColumn();
        move_cell(game, state, row.white_ply, shown);
        ImGui::TableNextColumn();
        move_cell(game, state, row.black_ply, shown);
    }
    ImGui::EndTable();
}

} // namespace sbm_viewer
