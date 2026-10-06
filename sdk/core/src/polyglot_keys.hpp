// Random numbers of the Polyglot book format, used by Board.hash (E46).
#pragma once

#include <array>
#include <cstdint>

namespace sbm {

// Index 64 * (2 * piece type + white) + square for pieces, 768 + castling bit index,
// 772 + en passant file, 780 if white is to move.
inline constexpr int kPolyglotKeyCount = 781;
inline constexpr int kPolyglotCastlingOffset = 768;
inline constexpr int kPolyglotEnPassantOffset = 772;
inline constexpr int kPolyglotWhiteToMoveIndex = 780;

extern const std::array<std::uint64_t, kPolyglotKeyCount> kPolyglotKeys;

} // namespace sbm
