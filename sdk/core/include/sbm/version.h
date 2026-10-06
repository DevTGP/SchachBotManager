/* Version of the core and of its C interface. */
#ifndef SBM_VERSION_H
#define SBM_VERSION_H

#include <stdint.h>

#include "sbm/export.h"

/* Increased on every incompatible change of the C interface. Bindings compare it with
 * sbm_abi_version() when loading the library and refuse to run on a mismatch. */
#define SBM_ABI_VERSION 1

SBM_BEGIN_DECLS

SBM_API int32_t sbm_abi_version(void);

/* SemVer of the core, equal to the SDK version (E36). Static string. */
SBM_API const char* sbm_version(void);

SBM_END_DECLS

#endif
