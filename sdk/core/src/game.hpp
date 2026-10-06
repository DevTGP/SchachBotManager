// A position with its move history (Board): making and taking back moves and null moves.
#pragma once

#include <vector>

#include "move.hpp"
#include "position.hpp"

namespace sbm {

struct HistoryEntry {
    Position before;
    Move move; // kNullMove for a null move
};

class Game {
public:
    Game() = default;
    explicit Game(const Position& position) : position_(position) {}

    const Position& position() const {
        return position_;
    }

    const std::vector<HistoryEntry>& history() const {
        return history_;
    }

    // Plays a legal move with complete flags. On an exception the game is unchanged.
    void make(Move move);
    void make_null();

    // Restores the position before the last entry; the history must not be empty.
    void undo();

private:
    Position position_;
    std::vector<HistoryEntry> history_;
};

} // namespace sbm
