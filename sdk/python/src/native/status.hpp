// Turns status codes of the C interface into the exceptions of sbm.errors (E49, E52).
#pragma once

#include <string>

#include "sbm/status.h"

namespace sbm_py {

// Raises the exception class `name` of sbm.errors with the given message.
[[noreturn]] void raise_error(const char* name, const std::string& message);

// Raises the exception belonging to a status other than SBM_OK; `what` names the call.
[[noreturn]] void raise_status(sbm_status status, const std::string& what);

inline void check(sbm_status status, const char* what) {
    if (status != SBM_OK) {
        raise_status(status, what);
    }
}

} // namespace sbm_py
