#include "sbm/status.h"

const char* sbm_status_name(sbm_status status) {
    switch (status) {
        case SBM_OK:
            return "ok";
        case SBM_INVALID_ARGUMENT:
            return "invalid_argument";
        case SBM_INVALID_FEN:
            return "invalid_fen";
        case SBM_INVALID_UCI:
            return "invalid_uci";
        case SBM_ILLEGAL_MOVE:
            return "illegal_move";
        case SBM_INVALID_STATE:
            return "invalid_state";
        case SBM_BUFFER_TOO_SMALL:
            return "buffer_too_small";
        case SBM_OUT_OF_MEMORY:
            return "out_of_memory";
        case SBM_INTERNAL_ERROR:
            return "internal_error";
        default:
            return "unknown";
    }
}
