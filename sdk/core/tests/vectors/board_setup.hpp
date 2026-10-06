// Boards of call vectors, built and read through the C interface.
#pragma once

#include <memory>
#include <string>

#include <nlohmann/json.hpp>

#include "sbm/sbm.h"

namespace sbm_test {

struct BoardDeleter {
    void operator()(sbm_board* board) const {
        sbm_board_free(board);
    }
};

using BoardPtr = std::unique_ptr<sbm_board, BoardDeleter>;

// Board.from_fen(fen), then each move with Board.parse_move and Board.make_move, or
// Board.make_null_move for 0000. Throws std::runtime_error if a step fails.
BoardPtr setup_board(const nlohmann::json& board);

// Board.fen; throws std::runtime_error if it fails.
std::string board_fen(const sbm_board* board);

} // namespace sbm_test
