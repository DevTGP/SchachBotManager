#include "output.hpp"

#include <algorithm>

namespace sbm::capi {

sbm_status write_text(std::string_view text, char* buffer, std::uint32_t size) {
    if (text.size() >= size) {
        if (size > 0) {
            buffer[0] = '\0';
        }
        return SBM_BUFFER_TOO_SMALL;
    }
    std::copy(text.begin(), text.end(), buffer);
    buffer[text.size()] = '\0';
    return SBM_OK;
}

sbm_status write_moves(
    std::span<const Move> moves, sbm_move* out, std::uint32_t capacity, std::uint32_t* count) {
    *count = static_cast<std::uint32_t>(moves.size());
    if (moves.size() > capacity) {
        return SBM_BUFFER_TOO_SMALL;
    }
    std::copy(moves.begin(), moves.end(), out);
    return SBM_OK;
}

} // namespace sbm::capi
