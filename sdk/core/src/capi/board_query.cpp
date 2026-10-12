// Board.piece_at, pieces, side_to_move, castling_rights, en_passant_square, the counters and
// king_square.
#include "sbm/board_query.h"

#include <algorithm>
#include <array>

#include "arguments.hpp"
#include "en_passant.hpp"
#include "guard.hpp"
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

sbm_status sbm_board_pieces(
    const sbm_board* board, sbm_color color, sbm_piece_type piece_type, sbm_square* squares,
    sbm_piece* pieces, uint32_t capacity, uint32_t* count) {
    if (board == nullptr || count == nullptr ||
        ((squares == nullptr || pieces == nullptr) && capacity != 0) ||
        !sbm::capi::valid_color_filter(color) || !sbm::capi::valid_piece_type_filter(piece_type)) {
        return SBM_INVALID_ARGUMENT;
    }
    return sbm::capi::guarded([&]() -> sbm_status {
        const sbm::Position& position = board->game.position();
        std::array<sbm_square, sbm::kSquareCount> found_squares{};
        std::array<sbm_piece, sbm::kSquareCount> found_pieces{};
        uint32_t found = 0;
        for (int square = 0; square < sbm::kSquareCount; ++square) {
            const int piece = position.piece_at(square);
            if (piece == sbm::kNoPiece ||
                (color != SBM_NO_COLOR && sbm::color_of(piece) != color) ||
                (piece_type != SBM_NO_PIECE_TYPE && sbm::type_of(piece) != piece_type)) {
                continue;
            }
            found_squares[found] = static_cast<sbm_square>(square);
            found_pieces[found] = static_cast<sbm_piece>(piece);
            ++found;
        }
        // As write_moves: the needed number, and the outputs unchanged if they are too small.
        *count = found;
        if (found > capacity) {
            return SBM_BUFFER_TOO_SMALL;
        }
        std::copy_n(found_squares.begin(), found, squares);
        std::copy_n(found_pieces.begin(), found, pieces);
        return SBM_OK;
    });
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
