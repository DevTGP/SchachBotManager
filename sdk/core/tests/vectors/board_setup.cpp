#include "board_setup.hpp"

#include <stdexcept>

namespace sbm_test {

namespace {

void expect_ok(sbm_status status, const std::string& step) {
    if (status != SBM_OK) {
        throw std::runtime_error(step + " failed with " + sbm_status_name(status));
    }
}

} // namespace

BoardPtr setup_board(const nlohmann::json& board) {
    const auto fen = board.at("fen").get<std::string>();
    sbm_board* created = nullptr;
    expect_ok(sbm_board_from_fen(fen.c_str(), &created), "from_fen " + fen);
    BoardPtr result(created);
    for (const auto& item : board.at("moves")) {
        const auto uci = item.get<std::string>();
        if (uci == "0000") {
            expect_ok(sbm_board_make_null_move(result.get()), "make_null_move");
            continue;
        }
        sbm_move move = 0;
        expect_ok(sbm_board_parse_move(result.get(), uci.c_str(), &move), "parse_move " + uci);
        expect_ok(sbm_board_make_move(result.get(), move), "make_move " + uci);
    }
    return result;
}

std::string board_fen(const sbm_board* board) {
    char fen[SBM_FEN_BUFFER_SIZE];
    expect_ok(sbm_board_fen(board, fen, sizeof fen), "fen");
    return fen;
}

} // namespace sbm_test
