// Shared shape of the functions that read one value from a board.
#pragma once

#include "board_handle.hpp"
#include "guard.hpp"

namespace sbm::capi {

// Checks the pointers, then stores the value returned by read(game) in *out.
template <typename T, typename Read>
sbm_status read_board(const sbm_board* board, T* out, Read&& read) noexcept {
    if (board == nullptr || out == nullptr) {
        return SBM_INVALID_ARGUMENT;
    }
    return guarded([&]() -> sbm_status {
        *out = static_cast<T>(read(board->game));
        return SBM_OK;
    });
}

} // namespace sbm::capi
