// Text and move list outputs with buffers that are too small, exact or absent (E51).
#include <array>
#include <cstdint>
#include <cstring>

#include "check.hpp"
#include "sbm/sbm.h"

namespace {

constexpr const char* kStart = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

void test_text() {
    sbm_board* board = nullptr;
    CHECK(sbm_board_new(&board) == SBM_OK);
    const auto length = static_cast<std::uint32_t>(std::strlen(kStart));

    std::array<char, SBM_FEN_BUFFER_SIZE> buffer{};
    buffer.fill('#');
    CHECK(sbm_board_fen(board, buffer.data(), length + 1) == SBM_OK);
    CHECK(std::strcmp(buffer.data(), kStart) == 0);

    buffer.fill('#');
    CHECK(sbm_board_fen(board, buffer.data(), length) == SBM_BUFFER_TOO_SMALL);
    CHECK(buffer[0] == '\0');

    buffer.fill('#');
    CHECK(sbm_board_fen(board, buffer.data(), 0) == SBM_BUFFER_TOO_SMALL);
    CHECK(buffer[0] == '#');

    std::array<char, SBM_UCI_BUFFER_SIZE> uci{};
    CHECK(sbm_move_uci(1804, uci.data(), 5) == SBM_OK);
    CHECK(std::strcmp(uci.data(), "e2e4") == 0);
    CHECK(sbm_move_uci(1804, uci.data(), 4) == SBM_BUFFER_TOO_SMALL);
    CHECK(sbm_move_uci(SBM_NULL_MOVE, uci.data(), SBM_UCI_BUFFER_SIZE) == SBM_INVALID_ARGUMENT);
    sbm_board_free(board);
}

void test_move_lists() {
    sbm_board* board = nullptr;
    CHECK(sbm_board_new(&board) == SBM_OK);
    std::array<sbm_move, SBM_MAX_MOVES> moves{};
    std::uint32_t count = 0;

    CHECK(sbm_board_legal_moves(board, nullptr, 0, &count) == SBM_BUFFER_TOO_SMALL);
    CHECK(count == 20);
    count = 0;
    moves.fill(0xABCD);
    CHECK(sbm_board_legal_moves(board, moves.data(), 19, &count) == SBM_BUFFER_TOO_SMALL);
    CHECK(count == 20);
    CHECK(moves[0] == 0xABCD);
    CHECK(sbm_board_legal_moves(board, moves.data(), 20, &count) == SBM_OK);
    CHECK(count == 20);
    CHECK(sbm_board_legal_moves(board, nullptr, 1, &count) == SBM_INVALID_ARGUMENT);
    CHECK(sbm_board_legal_moves(board, moves.data(), 20, nullptr) == SBM_INVALID_ARGUMENT);

    count = 99;
    CHECK(sbm_board_move_history(board, nullptr, 0, &count) == SBM_OK);
    CHECK(count == 0);
    sbm_move move = 0;
    CHECK(sbm_board_parse_move(board, "g1f3", &move) == SBM_OK);
    CHECK(sbm_board_make_move(board, move) == SBM_OK);
    CHECK(sbm_board_make_null_move(board) == SBM_OK);
    CHECK(sbm_board_move_history(board, nullptr, 0, &count) == SBM_BUFFER_TOO_SMALL);
    CHECK(count == 2);
    CHECK(sbm_board_move_history(board, moves.data(), 2, &count) == SBM_OK);
    CHECK(moves[0] == move && moves[1] == SBM_NULL_MOVE);
    sbm_board_free(board);
}

} // namespace

void test_buffers() {
    test_text();
    test_move_lists();
}
