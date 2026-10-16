// Turns status codes of the C interface into the error classes of src/errors.ts (E49, E52).
#pragma once

#include <string>

#include <napi.h>

#include "sbm/status.h"

namespace sbm_js {

// Throws the error class `name` of src/errors.ts with the given message.
[[noreturn]] void throw_error(Napi::Env env, const char* name, const std::string& message);

// Throws the error belonging to a status other than SBM_OK; `what` names the call.
[[noreturn]] void throw_status(Napi::Env env, sbm_status status, const std::string& what);

inline void check(Napi::Env env, sbm_status status, const char* what) {
    if (status != SBM_OK) {
        throw_status(env, status, what);
    }
}

} // namespace sbm_js
