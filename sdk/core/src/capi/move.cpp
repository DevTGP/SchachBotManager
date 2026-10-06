#include "sbm/move.h"

#include "guard.hpp"
#include "output.hpp"
#include "uci.hpp"

using sbm::capi::guarded;

sbm_status sbm_move_parse(const char* uci, sbm_move* out) {
    if (uci == nullptr || out == nullptr) {
        return SBM_INVALID_ARGUMENT;
    }
    return guarded([&]() -> sbm_status {
        const auto move = sbm::parse_uci(uci);
        if (!move) {
            return SBM_INVALID_UCI;
        }
        *out = *move;
        return SBM_OK;
    });
}

sbm_status sbm_move_uci(sbm_move move, char* buffer, uint32_t size) {
    if (buffer == nullptr) {
        return SBM_INVALID_ARGUMENT;
    }
    return guarded([&]() -> sbm_status {
        const auto text = sbm::write_uci(move);
        if (!text) {
            return SBM_INVALID_ARGUMENT;
        }
        return sbm::capi::write_text(*text, buffer, size);
    });
}
