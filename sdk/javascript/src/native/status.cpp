// Status codes of the C interface as errors of src/errors.ts (E49, E52).
#include "status.hpp"

#include "addon.hpp"

namespace sbm_js {

namespace {

struct ErrorKind {
    const char* name; // class in src/errors.ts, nullptr for statuses bot code never sees
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

void throw_error(Napi::Env env, const char* name, const std::string& message) {
    const Napi::ObjectReference& errors = addon_data(env).errors;
    if (errors.IsEmpty()) {
        throw Napi::Error::New(env, message);
    }
    const Napi::Value type = errors.Value().Get(name);
    if (!type.IsFunction()) {
        throw Napi::Error::New(env, message);
    }
    const Napi::Object error = type.As<Napi::Function>().New({Napi::String::New(env, message)});
    throw Napi::Error(env, error);
}

void throw_status(Napi::Env env, sbm_status status, const std::string& what) {
    if (status == SBM_OUT_OF_MEMORY) {
        throw Napi::RangeError::New(env, what + ": out of memory");
    }
    const ErrorKind kind = error_kind(status);
    if (kind.name == nullptr) {
        // SBM_BUFFER_TOO_SMALL and SBM_INTERNAL_ERROR are bugs of the binding or the core.
        throw_error(env, "ChessError", what + ": internal error (" + sbm_status_name(status) + ")");
    }
    throw_error(env, kind.name, what + ": " + kind.text);
}

} // namespace sbm_js
