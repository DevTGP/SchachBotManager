/* Status codes returned by the C interface (E49, E52). */
#ifndef SBM_STATUS_H
#define SBM_STATUS_H

#include <stdint.h>

#include "sbm/export.h"

typedef int32_t sbm_status;

enum {
    SBM_OK = 0,
    SBM_INVALID_ARGUMENT = 1, /* API error InvalidArgument; also a NULL pointer */
    SBM_INVALID_FEN = 2,      /* InvalidFen */
    SBM_INVALID_UCI = 3,      /* InvalidUci */
    SBM_ILLEGAL_MOVE = 4,     /* IllegalMove */
    SBM_INVALID_STATE = 5,    /* InvalidState */
    SBM_BUFFER_TOO_SMALL = 6, /* output buffer smaller than needed; never seen by bot code */
    SBM_OUT_OF_MEMORY = 7,    /* the language's out-of-memory error */
    SBM_INTERNAL_ERROR = 8    /* bug in the core; ChessError */
};

SBM_BEGIN_DECLS

/* Lower-case name of a status, e.g. "illegal_move"; "unknown" for other values.
 * The string is static and must not be freed. */
SBM_API const char* sbm_status_name(sbm_status status);

SBM_END_DECLS

#endif
