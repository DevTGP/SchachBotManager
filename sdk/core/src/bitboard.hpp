// Squares and bitboards: square = rank * 8 + file, bit n of a bitboard is square n (E35).
#pragma once

#include <bit>
#include <cstdint>

namespace sbm {

using Bitboard = std::uint64_t;

inline constexpr int kSquareCount = 64;
inline constexpr int kNoSquare = 64;

inline constexpr Bitboard kFileA = 0x0101010101010101ULL;
inline constexpr Bitboard kRank1 = 0xFFULL;
inline constexpr Bitboard kLightSquares = 0x55AA55AA55AA55AAULL;
inline constexpr Bitboard kDarkSquares = ~kLightSquares;

constexpr int file_of(int square) {
    return square & 7;
}

constexpr int rank_of(int square) {
    return square >> 3;
}

constexpr int make_square(int file, int rank) {
    return rank * 8 + file;
}

constexpr bool on_board(int file, int rank) {
    return file >= 0 && file < 8 && rank >= 0 && rank < 8;
}

constexpr Bitboard square_bb(int square) {
    return Bitboard{1} << square;
}

constexpr Bitboard file_bb(int file) {
    return kFileA << file;
}

constexpr Bitboard rank_bb(int rank) {
    return kRank1 << (8 * rank);
}

constexpr int popcount(Bitboard bitboard) {
    return std::popcount(bitboard);
}

// Lowest and highest square of a non-empty bitboard.
constexpr int lsb(Bitboard bitboard) {
    return std::countr_zero(bitboard);
}

constexpr int msb(Bitboard bitboard) {
    return 63 - std::countl_zero(bitboard);
}

// Removes the lowest square of a non-empty bitboard and returns it.
constexpr int pop_lsb(Bitboard& bitboard) {
    const int square = lsb(bitboard);
    bitboard &= bitboard - 1;
    return square;
}

} // namespace sbm
