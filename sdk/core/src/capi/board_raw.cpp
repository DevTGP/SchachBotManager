// Board.bitboard, bitboards, squares, occupied, occupied_by, piece_count and the attack queries.
#include "sbm/board_raw.h"

#include <algorithm>

#include "arguments.hpp"
#include "read_board.hpp"
#include "threats.hpp"

using sbm::Game;
using sbm::capi::read_board;
using sbm::capi::valid_color;
using sbm::capi::valid_piece_type;
using sbm::capi::valid_square;

namespace {

sbm::Color to_color(sbm_color color) {
    return static_cast<sbm::Color>(color);
}

sbm::PieceType to_type(sbm_piece_type piece_type) {
    return static_cast<sbm::PieceType>(piece_type);
}

} // namespace

sbm_status sbm_board_bitboard(
    const sbm_board* board, sbm_color color, sbm_piece_type piece_type, sbm_bitboard* out) {
    if (!valid_color(color) || !valid_piece_type(piece_type)) {
        return SBM_INVALID_ARGUMENT;
    }
    return read_board(board, out, [&](const Game& game) {
        return game.position().pieces_of(to_color(color), to_type(piece_type));
    });
}

sbm_status sbm_board_bitboards(const sbm_board* board, sbm_bitboard* out) {
    if (board == nullptr || out == nullptr) {
        return SBM_INVALID_ARGUMENT;
    }
    const auto& pieces = board->game.position().pieces;
    std::copy(pieces.begin(), pieces.end(), out);
    return SBM_OK;
}

sbm_status sbm_board_squares(const sbm_board* board, sbm_piece* out) {
    if (board == nullptr || out == nullptr) {
        return SBM_INVALID_ARGUMENT;
    }
    const auto& squares = board->game.position().squares;
    std::copy(squares.begin(), squares.end(), out);
    return SBM_OK;
}

sbm_status sbm_board_occupied(const sbm_board* board, sbm_bitboard* out) {
    return read_board(board, out, [](const Game& game) { return game.position().occupied(); });
}

sbm_status sbm_board_occupied_by(const sbm_board* board, sbm_color color, sbm_bitboard* out) {
    if (!valid_color(color)) {
        return SBM_INVALID_ARGUMENT;
    }
    return read_board(board, out, [&](const Game& game) { return game.position().colors[color]; });
}

sbm_status sbm_board_piece_count(
    const sbm_board* board, sbm_color color, sbm_piece_type piece_type, int32_t* out) {
    if (!valid_color(color) || !valid_piece_type(piece_type)) {
        return SBM_INVALID_ARGUMENT;
    }
    return read_board(board, out, [&](const Game& game) {
        return sbm::popcount(game.position().pieces_of(to_color(color), to_type(piece_type)));
    });
}

sbm_status sbm_board_attacks_from(const sbm_board* board, sbm_square square, sbm_bitboard* out) {
    if (!valid_square(square)) {
        return SBM_INVALID_ARGUMENT;
    }
    return read_board(
        board, out, [&](const Game& game) { return sbm::attacks_from(game.position(), square); });
}

sbm_status sbm_board_attackers_of(
    const sbm_board* board, sbm_square square, sbm_color color, sbm_bitboard* out) {
    if (!valid_square(square) || !valid_color(color)) {
        return SBM_INVALID_ARGUMENT;
    }
    return read_board(board, out, [&](const Game& game) {
        return sbm::attackers_of(game.position(), square, to_color(color));
    });
}

sbm_status
sbm_board_is_attacked(const sbm_board* board, sbm_square square, sbm_color color, sbm_bool* out) {
    if (!valid_square(square) || !valid_color(color)) {
        return SBM_INVALID_ARGUMENT;
    }
    return read_board(board, out, [&](const Game& game) {
        return sbm::is_attacked(game.position(), square, to_color(color));
    });
}

sbm_status sbm_board_checkers(const sbm_board* board, sbm_bitboard* out) {
    return read_board(board, out, [](const Game& game) { return sbm::checkers(game.position()); });
}

sbm_status sbm_board_pinned(const sbm_board* board, sbm_color color, sbm_bitboard* out) {
    if (!valid_color(color)) {
        return SBM_INVALID_ARGUMENT;
    }
    return read_board(board, out, [&](const Game& game) {
        return sbm::pinned(game.position(), to_color(color));
    });
}
