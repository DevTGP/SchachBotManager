#include "board_view.hpp"

#include <algorithm>
#include <cfloat>
#include <cmath>
#include <utility>

#include <imgui.h>

#include "theme.hpp"

namespace sbm_viewer {

namespace {

// Indexed by the core's piece type: pawn, knight, bishop, rook, queen, king.
constexpr const char* filled_glyphs[6] = {"♟", "♞", "♝", "♜", "♛", "♚"};
constexpr const char* outline_glyphs[6] = {"♙", "♘", "♗", "♖", "♕", "♔"};

void draw_centered(
    ImDrawList* draw, ImFont* font, float size, ImVec2 center, ImU32 color, const char* text) {
    const ImVec2 extent = font->CalcTextSizeA(size, FLT_MAX, 0.0f, text);
    draw->AddText(
        font, size, ImVec2(center.x - extent.x / 2.0f, center.y - extent.y / 2.0f), color, text);
}

// Squares of a move in UCI, or -1.
std::pair<int, int> move_squares(const std::string& uci) {
    if (uci.size() < 4) {
        return {-1, -1};
    }
    const auto square = [](char file, char rank) {
        if (file < 'a' || file > 'h' || rank < '1' || rank > '8') {
            return -1;
        }
        return (rank - '1') * 8 + (file - 'a');
    };
    return {square(uci[0], uci[1]), square(uci[2], uci[3])};
}

void draw_piece(ImDrawList* draw, ImFont* font, float size, ImVec2 center, int piece) {
    const int type = piece % 6;
    if (piece < 6) {
        draw_centered(draw, font, size, center, colors::white_piece, filled_glyphs[type]);
        draw_centered(draw, font, size, center, colors::black_piece, outline_glyphs[type]);
    } else {
        draw_centered(draw, font, size, center, colors::black_piece, filled_glyphs[type]);
    }
}

} // namespace

void draw_board(const GameRecord& game, int shown, bool white_bottom, ImFont* font, float size) {
    ImDrawList* draw = ImGui::GetWindowDrawList();
    const ImVec2 origin = ImGui::GetCursorScreenPos();
    const float square = std::floor(size / 8.0f);
    const Position& position = game.position(shown);
    const auto [from, to] = shown > 0 ? move_squares(game.ply(shown).uci) : std::pair{-1, -1};
    const int checked = position.checked_king();
    const float label_size = std::max(10.0f, square * 0.2f);

    for (int rank = 0; rank < 8; ++rank) {
        for (int file = 0; file < 8; ++file) {
            const int index = rank * 8 + file;
            const int column = white_bottom ? file : 7 - file;
            const int row = white_bottom ? 7 - rank : rank;
            const ImVec2 min(origin.x + column * square, origin.y + row * square);
            const ImVec2 max(min.x + square, min.y + square);
            const bool light = (rank + file) % 2 == 1;
            draw->AddRectFilled(min, max, light ? colors::light_square : colors::dark_square);
            if (index == from || index == to) {
                draw->AddRectFilled(min, max, colors::last_move);
            }
            if (index == checked) {
                draw->AddRectFilled(min, max, colors::check);
            }
            const ImU32 label_color = light ? colors::dark_square : colors::light_square;
            if (row == 7) {
                const char label[2] = {static_cast<char>('a' + file), '\0'};
                draw->AddText(
                    font, label_size, ImVec2(max.x - label_size * 0.7f, max.y - label_size * 1.1f),
                    label_color, label);
            }
            if (column == 0) {
                const char label[2] = {static_cast<char>('1' + rank), '\0'};
                draw->AddText(
                    font, label_size, ImVec2(min.x + 2.0f, min.y + 1.0f), label_color, label);
            }
            const int piece = position.piece_at(index);
            if (piece >= 0 && piece < 12) {
                draw_piece(
                    draw, font, square * 0.84f,
                    ImVec2(min.x + square / 2.0f, min.y + square / 2.0f), piece);
            }
        }
    }
    ImGui::Dummy(ImVec2(square * 8.0f, square * 8.0f));
}

} // namespace sbm_viewer
