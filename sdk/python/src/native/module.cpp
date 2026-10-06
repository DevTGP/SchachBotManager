// The native module sbm._core; the package sbm re-exports its classes.
#include <nanobind/nanobind.h>

#include "board.hpp"
#include "move.hpp"
#include "sbm/version.h"

namespace nb = nanobind;

NB_MODULE(_core, module) {
    if (sbm_abi_version() != SBM_ABI_VERSION) {
        throw nb::import_error("sbm._core: the chess core has another ABI version");
    }
    module.doc() = "Chess core of SchachBotManager (sdk/core) for Python.";
    module.def("core_version", &sbm_version, "SemVer of the chess core.");

    sbm_py::bind_move(module);
    sbm_py::BoardClass board(
        module, "Board", "A chess position with its move history.", nb::is_weak_referenceable());
    sbm_py::bind_board(board);
    sbm_py::bind_board_moves(board);
    sbm_py::bind_board_query(board);
    sbm_py::bind_board_raw(board);
    sbm_py::bind_board_state(board);
}
