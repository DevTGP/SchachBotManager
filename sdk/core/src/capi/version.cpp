#include "sbm/version.h"

// SBM_VERSION_STRING is the project version, set by CMake.
static_assert(sizeof(SBM_VERSION_STRING) > 1, "SBM_VERSION_STRING must not be empty");

int32_t sbm_abi_version(void) {
    return SBM_ABI_VERSION;
}

const char* sbm_version(void) {
    return SBM_VERSION_STRING;
}
