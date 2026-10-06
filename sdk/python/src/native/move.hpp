// Move: the 16-bit value of E34 as an immutable Python object.
#pragma once

#include <string>

#include <nanobind/nanobind.h>

#include "sbm/types.h"

namespace sbm_py {

struct Move {
    sbm_move value;
};

// Readable form for repr and error messages, e.g. <Move e2e4 flags=1>.
std::string move_repr(sbm_move value);

void bind_move(nanobind::module_& module);

} // namespace sbm_py
