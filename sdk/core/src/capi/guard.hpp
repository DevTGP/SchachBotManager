// Every C function runs its body through guarded: C++ exceptions never leave the core (E52).
#pragma once

#include <new>

#include "sbm/status.h"

namespace sbm::capi {

template <typename Body> sbm_status guarded(Body&& body) noexcept {
    try {
        return body();
    } catch (const std::bad_alloc&) {
        return SBM_OUT_OF_MEMORY;
    } catch (...) {
        return SBM_INTERNAL_ERROR;
    }
}

} // namespace sbm::capi
