// Board.legal_moves to Board.undo_null_move.
#include "sbm/board_moves.h"

#include "board_handle.hpp"
#include "guard.hpp"
#include "movegen.hpp"
#include "output.hpp"
#include "san.hpp"
#include "threats.hpp"
#include "uci.hpp"

static_assert(sbm::kMaxMoves == SBM_MAX_MOVES, "move list capacity of the C interface");

using sbm::capi::guarded;

namespace {

using Generate = void (*)(const sbm::Position&, sbm::MoveList&);

sbm_status generated_moves(
    const sbm_board* board, Generate generate, sbm_move* out, uint32_t capacity, uint32_t* count) {
    if (board == nullptr || !sbm::capi::valid_move_output(out, capacity, count)) {
        return SBM_INVALID_ARGUMENT;
    }
    return guarded([&]() -> sbm_status {
        sbm::MoveList list;
        generate(board->game.position(), list);
        return sbm::capi::write_moves(
            {list.begin(), static_cast<std::size_t>(list.size)}, out, capacity, count);
    });
}

} // namespace

sbm_status
sbm_board_legal_moves(const sbm_board* board, sbm_move* out, uint32_t capacity, uint32_t* count) {
    return generated_moves(board, sbm::generate_legal_moves, out, capacity, count);
}

sbm_status sbm_board_legal_captures(
    const sbm_board* board, sbm_move* out, uint32_t capacity, uint32_t* count) {
    return generated_moves(board, sbm::generate_legal_captures, out, capacity, count);
}

sbm_status sbm_board_is_legal(const sbm_board* board, sbm_move move, sbm_bool* out) {
    if (board == nullptr || out == nullptr) {
        return SBM_INVALID_ARGUMENT;
    }
    return guarded([&]() -> sbm_status {
        *out = sbm::find_legal_move(board->game.position(), move).has_value() ? 1 : 0;
        return SBM_OK;
    });
}

sbm_status sbm_board_parse_move(const sbm_board* board, const char* uci, sbm_move* out) {
    if (board == nullptr || uci == nullptr || out == nullptr) {
        return SBM_INVALID_ARGUMENT;
    }
    return guarded([&]() -> sbm_status {
        const auto move = sbm::parse_uci(uci);
        if (!move) {
            return SBM_INVALID_UCI;
        }
        const auto legal = sbm::find_legal_move(board->game.position(), *move);
        if (!legal) {
            return SBM_ILLEGAL_MOVE;
        }
        *out = *legal;
        return SBM_OK;
    });
}

sbm_status sbm_board_san(const sbm_board* board, sbm_move move, char* buffer, uint32_t size) {
    if (board == nullptr || buffer == nullptr) {
        return SBM_INVALID_ARGUMENT;
    }
    return guarded([&]() -> sbm_status {
        const sbm::Position& position = board->game.position();
        const auto legal = sbm::find_legal_move(position, move);
        if (!legal) {
            return SBM_ILLEGAL_MOVE;
        }
        return sbm::capi::write_text(sbm::write_san(position, *legal), buffer, size);
    });
}

sbm_status sbm_board_make_move(sbm_board* board, sbm_move move) {
    if (board == nullptr) {
        return SBM_INVALID_ARGUMENT;
    }
    return guarded([&]() -> sbm_status {
        const auto legal = sbm::find_legal_move(board->game.position(), move);
        if (!legal) {
            return SBM_ILLEGAL_MOVE;
        }
        board->game.make(*legal);
        return SBM_OK;
    });
}

sbm_status sbm_board_undo_move(sbm_board* board) {
    if (board == nullptr) {
        return SBM_INVALID_ARGUMENT;
    }
    const auto& history = board->game.history();
    if (history.empty() || history.back().move == sbm::kNullMove) {
        return SBM_INVALID_STATE;
    }
    board->game.undo();
    return SBM_OK;
}

sbm_status sbm_board_make_null_move(sbm_board* board) {
    if (board == nullptr) {
        return SBM_INVALID_ARGUMENT;
    }
    return guarded([&]() -> sbm_status {
        if (sbm::checkers(board->game.position()) != 0) {
            return SBM_INVALID_STATE;
        }
        board->game.make_null();
        return SBM_OK;
    });
}

sbm_status sbm_board_undo_null_move(sbm_board* board) {
    if (board == nullptr) {
        return SBM_INVALID_ARGUMENT;
    }
    const auto& history = board->game.history();
    if (history.empty() || history.back().move != sbm::kNullMove) {
        return SBM_INVALID_STATE;
    }
    board->game.undo();
    return SBM_OK;
}
