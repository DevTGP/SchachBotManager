#include "frame.hpp"

#include <algorithm>

#include <imgui.h>

#include "board_view.hpp"
#include "controls.hpp"
#include "details_view.hpp"
#include "game_bar.hpp"
#include "log_view.hpp"
#include "move_list.hpp"
#include "players_view.hpp"

namespace sbm_viewer {

namespace {

constexpr ImGuiWindowFlags frame_flags = ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_NoMove |
                                         ImGuiWindowFlags_NoSavedSettings |
                                         ImGuiWindowFlags_NoBringToFrontOnFocus;

// `newest` is false for an earlier game: its clocks no longer run.
PlayerBar
player(const GameRecord& game, const ViewState& state, bool white, bool newest, uint64_t now_ms) {
    const int count = game.ply_count();
    const int shown = state.navigation.shown(count);
    const StartMessage& start = game.start();
    const bool bot = game.bot_is_white() == white;
    const Clocks clocks = game.clocks(shown);

    PlayerBar bar;
    bar.name = bot ? start.bot : start.opponent;
    bar.is_bot = bot;
    bar.white = white;
    bar.clock_ms = white ? clocks.white_ms : clocks.black_ms;
    bar.to_move = (game.position(shown).side_to_move() == SBM_WHITE) == white;
    bar.running =
        bar.to_move && newest && state.navigation.live() && !game.result() && !state.input_closed;
    if (bar.running && bar.clock_ms) {
        const int64_t passed = static_cast<int64_t>(now_ms - state.changed_at_ms);
        bar.clock_ms = std::max<int64_t>(0, *bar.clock_ms - passed);
    }
    return bar;
}

void draw_board_side(
    const GameRecord& game, ViewState& state, ImFont* font, uint64_t now_ms, bool newest) {
    const ImVec2 avail = ImGui::GetContentRegionAvail();
    const ImGuiStyle& style = ImGui::GetStyle();
    const float controls = ImGui::GetFrameHeight() + style.ItemSpacing.y;
    const float size =
        std::max(64.0f, std::min(avail.x, avail.y - 2.0f * player_bar_height() - controls));
    const bool white_bottom = game.bot_is_white() != state.flipped;

    draw_player_bar(player(game, state, !white_bottom, newest, now_ms), size);
    draw_board(game, state.navigation.shown(game.ply_count()), white_bottom, font, size);
    const bool board_hovered = ImGui::IsItemHovered();
    draw_player_bar(player(game, state, white_bottom, newest, now_ms), size);
    draw_controls(game, state);
    handle_keys(game, state, board_hovered);
}

void draw_info_side(const Session& session, ViewState& state) {
    const auto& games = session.games();
    const GameRecord& game = games[static_cast<size_t>(state.navigation.game())];
    draw_game_bar(games, state);
    ImGui::Separator();

    const float spacing = ImGui::GetStyle().ItemSpacing.y;
    const float rest = ImGui::GetContentRegionAvail().y;
    const float moves = std::max(80.0f, rest * 0.42f);
    draw_move_list(game, state, moves);

    ImGui::Separator();
    const float details_top = ImGui::GetCursorPosY();
    draw_details(game, state.navigation.shown(game.ply_count()));
    ImGui::Separator();
    const float used = ImGui::GetCursorPosY() - details_top + spacing;
    draw_log(game, state, std::max(60.0f, rest - moves - used - spacing * 2.0f));
}

} // namespace

void draw_frame(const Session& session, ViewState& state, ImFont* font, uint64_t now_ms) {
    const ImGuiViewport* viewport = ImGui::GetMainViewport();
    ImGui::SetNextWindowPos(viewport->WorkPos);
    ImGui::SetNextWindowSize(viewport->WorkSize);
    ImGui::Begin("viewer", nullptr, frame_flags);

    const auto& games = session.games();
    if (games.empty()) {
        ImGui::TextDisabled(
            state.input_closed ? "The bot program ended without a game."
                               : "Waiting for the bot's game…");
        ImGui::End();
        return;
    }
    const int index = state.navigation.game();
    const GameRecord& game = games[static_cast<size_t>(index)];
    const bool newest = index == static_cast<int>(games.size()) - 1;

    const float scale = ImGui::GetStyle().FontSizeBase / 16.0f;
    const float avail = ImGui::GetContentRegionAvail().x;
    const float info_width = std::clamp(avail * 0.38f, 300.0f * scale, 480.0f * scale);

    ImGui::BeginChild(
        "board side", ImVec2(avail - info_width - ImGui::GetStyle().ItemSpacing.x, 0));
    draw_board_side(game, state, font, now_ms, newest);
    ImGui::EndChild();
    ImGui::SameLine();
    ImGui::BeginChild("info side", ImVec2(0, 0));
    draw_info_side(session, state);
    ImGui::EndChild();

    ImGui::End();
}

} // namespace sbm_viewer
