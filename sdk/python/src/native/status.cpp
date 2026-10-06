// Status codes of the C interface as exceptions of sbm.errors (E49, E52).
#include "status.hpp"

#include <new>

#include <nanobind/nanobind.h>

namespace nb = nanobind;

namespace sbm_py {

namespace {

struct ErrorKind {
    const char* name; // class in sbm.errors, nullptr for statuses bot code never sees
    const char* text;
};

ErrorKind error_kind(sbm_status status) {
    switch (status) {
        case SBM_INVALID_ARGUMENT:
            return {"InvalidArgumentError", "invalid argument"};
        case SBM_INVALID_FEN:
            return {"InvalidFenError", "invalid FEN"};
        case SBM_INVALID_UCI:
            return {"InvalidUciError", "not a move in UCI notation"};
        case SBM_ILLEGAL_MOVE:
            return {"IllegalMoveError", "illegal move"};
        case SBM_INVALID_STATE:
            return {"InvalidStateError", "not possible in the current state"};
        default:
            return {nullptr, nullptr};
    }
}

} // namespace

void raise_error(const char* name, const std::string& message) {
    // Looked up on demand, so the module imports without the package (stub generation).
    const nb::object type = nb::module_::import_("sbm.errors").attr(name);
    PyErr_SetString(type.ptr(), message.c_str());
    throw nb::python_error();
}

void raise_status(sbm_status status, const std::string& what) {
    if (status == SBM_OUT_OF_MEMORY) {
        throw std::bad_alloc(); // nanobind raises MemoryError
    }
    const ErrorKind kind = error_kind(status);
    if (kind.name == nullptr) {
        // SBM_BUFFER_TOO_SMALL and SBM_INTERNAL_ERROR are bugs of the binding or the core.
        raise_error("ChessError", what + ": internal error (" + sbm_status_name(status) + ")");
    }
    raise_error(kind.name, what + ": " + kind.text);
}

} // namespace sbm_py
