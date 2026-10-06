// Handles, status codes, versions, NULL pointers and unchanged outputs on errors.
#include <cstring>

#include "check.hpp"
#include "sbm/sbm.h"

namespace {

constexpr const char* kStart = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

bool fen_is(const sbm_board* board, const char* expected) {
    char fen[SBM_FEN_BUFFER_SIZE];
    return sbm_board_fen(board, fen, sizeof fen) == SBM_OK && std::strcmp(fen, expected) == 0;
}

void test_versions_and_status_names() {
    CHECK(sbm_abi_version() == SBM_ABI_VERSION);
    CHECK(std::strcmp(sbm_version(), SBM_EXPECTED_VERSION) == 0);
    CHECK(std::strcmp(sbm_status_name(SBM_OK), "ok") == 0);
    CHECK(std::strcmp(sbm_status_name(SBM_ILLEGAL_MOVE), "illegal_move") == 0);
    CHECK(std::strcmp(sbm_status_name(SBM_INTERNAL_ERROR), "internal_error") == 0);
    CHECK(std::strcmp(sbm_status_name(9), "unknown") == 0);
    CHECK(std::strcmp(sbm_status_name(-1), "unknown") == 0);
}

void test_null_pointers() {
    sbm_board* board = nullptr;
    CHECK(sbm_board_new(nullptr) == SBM_INVALID_ARGUMENT);
    CHECK(sbm_board_from_fen(nullptr, &board) == SBM_INVALID_ARGUMENT);
    CHECK(sbm_board_from_fen(kStart, nullptr) == SBM_INVALID_ARGUMENT);
    CHECK(sbm_board_copy(nullptr, &board) == SBM_INVALID_ARGUMENT);
    CHECK(board == nullptr);
    sbm_board_free(nullptr);

    sbm_bool flag = 0;
    sbm_move move = 0;
    char text[SBM_FEN_BUFFER_SIZE];
    CHECK(sbm_board_is_check(nullptr, &flag) == SBM_INVALID_ARGUMENT);
    CHECK(sbm_board_make_move(nullptr, 0) == SBM_INVALID_ARGUMENT);
    CHECK(sbm_board_undo_move(nullptr) == SBM_INVALID_ARGUMENT);
    CHECK(sbm_board_fen(nullptr, text, sizeof text) == SBM_INVALID_ARGUMENT);
    CHECK(sbm_move_parse(nullptr, &move) == SBM_INVALID_ARGUMENT);
    CHECK(sbm_move_parse("e2e4", nullptr) == SBM_INVALID_ARGUMENT);
    CHECK(sbm_move_uci(1804, nullptr, 0) == SBM_INVALID_ARGUMENT);

    CHECK(sbm_board_new(&board) == SBM_OK);
    CHECK(sbm_board_is_check(board, nullptr) == SBM_INVALID_ARGUMENT);
    CHECK(sbm_board_fen(board, nullptr, 0) == SBM_INVALID_ARGUMENT);
    CHECK(sbm_board_parse_move(board, nullptr, &move) == SBM_INVALID_ARGUMENT);
    CHECK(sbm_board_bitboards(board, nullptr) == SBM_INVALID_ARGUMENT);
    CHECK(sbm_board_squares(board, nullptr) == SBM_INVALID_ARGUMENT);
    sbm_board_free(board);
}

void test_unchanged_outputs_on_error() {
    static int sentinel = 0;
    sbm_board* board = reinterpret_cast<sbm_board*>(&sentinel);
    sbm_board* const marker = board;
    CHECK(sbm_board_from_fen("8/8/8/8/8/8/8/8 w - - 0 1", &board) == SBM_INVALID_FEN);
    CHECK(board == marker);

    CHECK(sbm_board_new(&board) == SBM_OK);
    sbm_piece piece = 99;
    CHECK(sbm_board_piece_at(board, 64, &piece) == SBM_INVALID_ARGUMENT);
    CHECK(piece == 99);
    sbm_move move = 1234;
    CHECK(sbm_board_parse_move(board, "e2e5", &move) == SBM_ILLEGAL_MOVE);
    CHECK(sbm_board_parse_move(board, "e2", &move) == SBM_INVALID_UCI);
    CHECK(move == 1234);
    CHECK(sbm_board_make_move(board, 0x7000 | 1804) == SBM_ILLEGAL_MOVE);
    CHECK(fen_is(board, kStart));
    sbm_bool flag = 7;
    CHECK(sbm_board_is_repetition(board, 0, &flag) == SBM_INVALID_ARGUMENT);
    CHECK(flag == 7);
    sbm_board_free(board);
}

void test_copy_is_independent() {
    sbm_board* board = nullptr;
    CHECK(sbm_board_new(&board) == SBM_OK);
    sbm_move move = 0;
    CHECK(sbm_board_parse_move(board, "e2e4", &move) == SBM_OK);
    CHECK(sbm_board_make_move(board, move) == SBM_OK);

    sbm_board* copy = nullptr;
    CHECK(sbm_board_copy(board, &copy) == SBM_OK);
    CHECK(sbm_board_undo_move(copy) == SBM_OK);
    CHECK(fen_is(copy, kStart));
    CHECK(sbm_board_undo_move(copy) == SBM_INVALID_STATE);
    CHECK(fen_is(board, "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"));
    CHECK(sbm_board_undo_move(board) == SBM_OK);
    sbm_board_free(copy);
    sbm_board_free(board);
}

void test_null_move_history() {
    sbm_board* board = nullptr;
    CHECK(sbm_board_new(&board) == SBM_OK);
    CHECK(sbm_board_undo_null_move(board) == SBM_INVALID_STATE);
    CHECK(sbm_board_make_null_move(board) == SBM_OK);
    CHECK(sbm_board_undo_move(board) == SBM_INVALID_STATE);
    CHECK(sbm_board_undo_null_move(board) == SBM_OK);
    CHECK(fen_is(board, kStart));
    sbm_board_free(board);
}

} // namespace

void test_handles() {
    test_versions_and_status_names();
    test_null_pointers();
    test_unchanged_outputs_on_error();
    test_copy_is_independent();
    test_null_move_history();
}
