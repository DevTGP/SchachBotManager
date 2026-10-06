// Text and move list outputs with the buffer rules of E51.
#pragma once

#include <cstdint>
#include <span>
#include <string_view>

#include "move.hpp"
#include "sbm/status.h"
#include "sbm/types.h"

namespace sbm::capi {

// Whether the pointers of a move list output are acceptable: out may be NULL only with
// capacity 0.
constexpr bool
valid_move_output(const sbm_move* out, std::uint32_t capacity, const std::uint32_t* count) {
    return count != nullptr && (out != nullptr || capacity == 0);
}

// Copies the text with its NUL. If it does not fit: SBM_BUFFER_TOO_SMALL and, for size > 0,
// the empty text. The buffer must not be NULL.
sbm_status write_text(std::string_view text, char* buffer, std::uint32_t size);

// Copies the moves and stores their number. If they do not fit: SBM_BUFFER_TOO_SMALL, the
// needed number in *count and out unchanged.
sbm_status write_moves(
    std::span<const Move> moves, sbm_move* out, std::uint32_t capacity, std::uint32_t* count);

} // namespace sbm::capi
