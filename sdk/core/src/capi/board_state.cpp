// End conditions: Board.is_check to Board.is_game_over.
#include "sbm/board_state.h"

#include "arguments.hpp"
#include "end_conditions.hpp"
#include "material.hpp"
#include "read_board.hpp"
#include "repetition.hpp"

using sbm::Game;
using sbm::capi::read_board;

sbm_status sbm_board_is_check(const sbm_board* board, sbm_bool* out) {
    return read_board(board, out, [](const Game& game) { return sbm::is_check(game.position()); });
}

sbm_status sbm_board_is_checkmate(const sbm_board* board, sbm_bool* out) {
    return read_board(
        board, out, [](const Game& game) { return sbm::is_checkmate(game.position()); });
}

sbm_status sbm_board_is_stalemate(const sbm_board* board, sbm_bool* out) {
    return read_board(
        board, out, [](const Game& game) { return sbm::is_stalemate(game.position()); });
}

sbm_status sbm_board_is_repetition(const sbm_board* board, int32_t count, sbm_bool* out) {
    if (count < 1) {
        return SBM_INVALID_ARGUMENT;
    }
    return read_board(
        board, out, [&](const Game& game) { return sbm::repetition_count(game) >= count; });
}

sbm_status sbm_board_is_fifty_move_rule(const sbm_board* board, sbm_bool* out) {
    return read_board(
        board, out, [](const Game& game) { return sbm::is_fifty_move_rule(game.position()); });
}

sbm_status sbm_board_is_insufficient_material(const sbm_board* board, sbm_bool* out) {
    return read_board(board, out, [](const Game& game) {
        return sbm::is_insufficient_material(game.position());
    });
}

sbm_status
sbm_board_has_insufficient_material(const sbm_board* board, sbm_color color, sbm_bool* out) {
    if (!sbm::capi::valid_color(color)) {
        return SBM_INVALID_ARGUMENT;
    }
    return read_board(board, out, [&](const Game& game) {
        return sbm::has_insufficient_material(game.position(), static_cast<sbm::Color>(color));
    });
}

sbm_status sbm_board_is_draw(const sbm_board* board, sbm_bool* out) {
    return read_board(board, out, [](const Game& game) { return sbm::is_draw(game); });
}

sbm_status sbm_board_is_game_over(const sbm_board* board, sbm_bool* out) {
    return read_board(board, out, [](const Game& game) { return sbm::is_game_over(game); });
}
