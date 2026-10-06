// Board.piece_at, side_to_move, castling_rights, en_passant_square, the counters and king_square.
#include "sbm/board_query.h"

#include "arguments.hpp"
#include "en_passant.hpp"
#include "read_board.hpp"

using sbm::Game;
using sbm::capi::read_board;

sbm_status sbm_board_piece_at(const sbm_board* board, sbm_square square, sbm_piece* out) {
    if (!sbm::capi::valid_square(square)) {
        return SBM_INVALID_ARGUMENT;
    }
    return read_board(
        board, out, [&](const Game& game) { return game.position().piece_at(square); });
}

sbm_status sbm_board_side_to_move(const sbm_board* board, sbm_color* out) {
    return read_board(board, out, [](const Game& game) { return game.position().side_to_move; });
}

sbm_status sbm_board_castling_rights(const sbm_board* board, sbm_castling* out) {
    return read_board(board, out, [](const Game& game) { return game.position().castling; });
}

sbm_status sbm_board_en_passant_square(const sbm_board* board, sbm_square* out) {
    return read_board(
        board, out, [](const Game& game) { return sbm::legal_en_passant_square(game.position()); });
}

sbm_status sbm_board_halfmove_clock(const sbm_board* board, int32_t* out) {
    return read_board(board, out, [](const Game& game) { return game.position().halfmove_clock; });
}

sbm_status sbm_board_fullmove_number(const sbm_board* board, int32_t* out) {
    return read_board(board, out, [](const Game& game) { return game.position().fullmove_number; });
}

sbm_status sbm_board_king_square(const sbm_board* board, sbm_color color, sbm_square* out) {
    if (!sbm::capi::valid_color(color)) {
        return SBM_INVALID_ARGUMENT;
    }
    return read_board(board, out, [&](const Game& game) {
        return game.position().king_square(static_cast<sbm::Color>(color));
    });
}
