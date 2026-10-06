// Fixed-capacity list of moves; no position has more legal moves than kMaxMoves.
#pragma once

#include <array>

#include "move.hpp"

namespace sbm {

inline constexpr int kMaxMoves = 256;

struct MoveList {
    std::array<Move, kMaxMoves> moves;
    int size = 0;

    void add(Move move) {
        moves[size++] = move;
    }

    const Move* begin() const {
        return moves.data();
    }

    const Move* end() const {
        return moves.data() + size;
    }
};

} // namespace sbm
