#include "details_view.hpp"

#include <string>

#include <imgui.h>

#include "model/notation.hpp"
#include "model/time_text.hpp"

namespace sbm_viewer {

namespace {

void draw_info(const SearchInfo& info, const Position& before) {
    std::string line;
    if (info.depth) {
        line += "Depth " + std::to_string(*info.depth);
        if (info.seldepth) {
            line += "/" + std::to_string(*info.seldepth);
        }
        line += "   ";
    }
    const std::string score = score_text(info);
    if (!score.empty()) {
        line += "Score " + score + "   ";
    }
    if (info.nodes) {
        line += "Nodes " + nodes_text(*info.nodes);
    }
    if (!line.empty()) {
        ImGui::TextUnformatted(line.c_str());
    }
    const std::string pv = pv_text(before, info.pv);
    if (!pv.empty()) {
        ImGui::TextWrapped("PV: %s", pv.c_str());
    }
    if (!info.text.empty()) {
        ImGui::TextWrapped("%s", info.text.c_str());
    }
}

} // namespace

void draw_details(const GameRecord& game, int shown) {
    if (shown == 0) {
        ImGui::TextUnformatted("Start position");
    } else {
        const PlyRecord& record = game.ply(shown);
        const Position& before = game.position(shown - 1);
        const bool white_moved = before.side_to_move() == SBM_WHITE;
        ImGui::Text(
            "%d%s %s", before.fullmove_number(), white_moved ? "." : "...", record.san.c_str());
        ImGui::SameLine();
        ImGui::TextDisabled(record.by_bot ? "by the bot" : "by the opponent");
        if (record.elapsed_ms) {
            ImGui::Text("Thinking time %s", duration_text(*record.elapsed_ms).c_str());
        }
        if (record.info) {
            draw_info(*record.info, before);
        }
    }
    const std::string fen = game.position(shown).fen();
    if (ImGui::SmallButton("Copy FEN")) {
        ImGui::SetClipboardText(fen.c_str());
    }
    ImGui::SameLine();
    ImGui::TextDisabled("%s", fen.c_str());
}

} // namespace sbm_viewer
