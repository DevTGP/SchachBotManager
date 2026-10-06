// Calls a C function that writes one value of a board and returns it.
#pragma once

#include "board.hpp"
#include "status.hpp"

namespace sbm_py {

// function(handle, args..., &out); `what` names the API function for error messages.
template <typename T, typename Function, typename... Args>
T query(Function function, const Board& board, const char* what, Args... args) {
    T out{};
    check(function(board.get(), args..., &out), what);
    return out;
}

} // namespace sbm_py
