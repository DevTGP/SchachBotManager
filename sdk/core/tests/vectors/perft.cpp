#include "perft.hpp"

#include <array>
#include <cstdint>
#include <exception>
#include <stdexcept>
#include <string>

#include "board_setup.hpp"

namespace sbm_test {

namespace {

void expect_ok(sbm_status status, const char* function) {
    if (status != SBM_OK) {
        throw std::runtime_error(std::string(function) + " failed with " + sbm_status_name(status));
    }
}

// Leaf nodes of the legal move tree, counting the moves at depth 1 without making them.
std::uint64_t perft(sbm_board* board, int depth) {
    std::array<sbm_move, SBM_MAX_MOVES> moves;
    std::uint32_t count = 0;
    expect_ok(sbm_board_legal_moves(board, moves.data(), SBM_MAX_MOVES, &count), "legal_moves");
    if (depth == 1) {
        return count;
    }
    std::uint64_t nodes = 0;
    for (std::uint32_t i = 0; i < count; ++i) {
        expect_ok(sbm_board_make_move(board, moves[i]), "make_move");
        nodes += perft(board, depth - 1);
        expect_ok(sbm_board_undo_move(board), "undo_move");
    }
    return nodes;
}

} // namespace

void run_perft_vectors(const nlohmann::json& file, bool slow, Summary& summary) {
    for (const auto& vector : file.at("vectors")) {
        const auto id = vector.at("id").get<std::string>();
        if (vector.value("slow", false) && !slow) {
            summary.skip();
            continue;
        }
        try {
            const auto fen = vector.at("fen").get<std::string>();
            const BoardPtr board = setup_board({{"fen", fen}, {"moves", nlohmann::json::array()}});
            const auto expected = vector.at("nodes").get<std::uint64_t>();
            const auto actual = perft(board.get(), vector.at("depth").get<int>());
            if (actual == expected) {
                summary.pass();
            } else {
                summary.fail(
                    id, "expected " + std::to_string(expected) + " nodes, got " +
                            std::to_string(actual));
            }
        } catch (const std::exception& error) {
            summary.fail(id, error.what());
        }
    }
}

} // namespace sbm_test
