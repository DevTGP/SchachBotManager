// Board.create, from_fen, copy, fen, hash, move_history and to_text.
#include "sbm/board.h"

#include <vector>

#include "board_handle.hpp"
#include "fen.hpp"
#include "guard.hpp"
#include "hash.hpp"
#include "output.hpp"
#include "position.hpp"
#include "text.hpp"

using sbm::capi::guarded;

sbm_status sbm_board_new(sbm_board** out) {
    if (out == nullptr) {
        return SBM_INVALID_ARGUMENT;
    }
    return guarded([&]() -> sbm_status {
        *out = new sbm_board{sbm::Game(sbm::start_position())};
        return SBM_OK;
    });
}

sbm_status sbm_board_from_fen(const char* fen, sbm_board** out) {
    if (fen == nullptr || out == nullptr) {
        return SBM_INVALID_ARGUMENT;
    }
    return guarded([&]() -> sbm_status {
        const auto position = sbm::parse_fen(fen);
        if (!position) {
            return SBM_INVALID_FEN;
        }
        *out = new sbm_board{sbm::Game(*position)};
        return SBM_OK;
    });
}

sbm_status sbm_board_copy(const sbm_board* board, sbm_board** out) {
    if (board == nullptr || out == nullptr) {
        return SBM_INVALID_ARGUMENT;
    }
    return guarded([&]() -> sbm_status {
        *out = new sbm_board{*board};
        return SBM_OK;
    });
}

void sbm_board_free(sbm_board* board) {
    delete board;
}

sbm_status sbm_board_fen(const sbm_board* board, char* buffer, uint32_t size) {
    if (board == nullptr || buffer == nullptr) {
        return SBM_INVALID_ARGUMENT;
    }
    return guarded([&]() -> sbm_status {
        return sbm::capi::write_text(sbm::write_fen(board->game.position()), buffer, size);
    });
}

sbm_status sbm_board_hash(const sbm_board* board, uint64_t* out) {
    if (board == nullptr || out == nullptr) {
        return SBM_INVALID_ARGUMENT;
    }
    *out = sbm::polyglot_hash(board->game.position());
    return SBM_OK;
}

sbm_status
sbm_board_move_history(const sbm_board* board, sbm_move* out, uint32_t capacity, uint32_t* count) {
    if (board == nullptr || !sbm::capi::valid_move_output(out, capacity, count)) {
        return SBM_INVALID_ARGUMENT;
    }
    return guarded([&]() -> sbm_status {
        std::vector<sbm::Move> moves;
        moves.reserve(board->game.history().size());
        for (const sbm::HistoryEntry& entry : board->game.history()) {
            moves.push_back(entry.move);
        }
        return sbm::capi::write_moves(moves, out, capacity, count);
    });
}

sbm_status sbm_board_to_text(const sbm_board* board, char* buffer, uint32_t size) {
    if (board == nullptr || buffer == nullptr) {
        return SBM_INVALID_ARGUMENT;
    }
    return guarded([&]() -> sbm_status {
        return sbm::capi::write_text(sbm::write_text(board->game.position()), buffer, size);
    });
}
