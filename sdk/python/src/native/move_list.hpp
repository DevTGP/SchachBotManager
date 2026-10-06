// Move values of the C interface as a Python list of Move objects.
#pragma once

#include <cstdint>

#include <nanobind/nanobind.h>

#include "move.hpp"

namespace sbm_py {

// Typed so that the generated stubs read list[Move].
using MoveList = nanobind::typed<nanobind::list, Move>;

inline MoveList move_list(const sbm_move* moves, std::uint32_t count) {
    MoveList result;
    for (std::uint32_t i = 0; i < count; ++i) {
        result.append(nanobind::cast(Move{moves[i]}));
    }
    return result;
}

} // namespace sbm_py
