#include "repetition.hpp"

#include "en_passant.hpp"

namespace sbm {

namespace {

bool same_position(const Position& a, const Position& b) {
    return a.squares == b.squares && a.side_to_move == b.side_to_move && a.castling == b.castling &&
           legal_en_passant_square(a) == legal_en_passant_square(b);
}

} // namespace

int repetition_count(const Game& game) {
    int count = 1;
    for (const HistoryEntry& entry : game.history()) {
        if (same_position(entry.before, game.position())) {
            ++count;
        }
    }
    return count;
}

} // namespace sbm
