// Which game and half-move the window shows: live follows the newest state, otherwise the view
// stays where the user stepped to.
#pragma once

#include <optional>

namespace sbm_viewer {

class Navigation {
public:
    // Half-move shown in a game with `count` half-moves.
    int shown(int count) const;
    bool live() const {
        return !pinned_;
    }

    // Going to the last half-move or beyond makes the view live again.
    void go_to(int ply, int count);
    void step(int delta, int count);
    void first(int count);
    void last();

    int game() const {
        return game_;
    }
    // Shows another game from its end; choosing the newest one follows new games again.
    void select_game(int index, int game_count);
    // Called when games arrive: a view that follows switches to the newest game.
    void games_changed(int game_count);

private:
    std::optional<int> pinned_;
    int game_ = 0;
    bool follow_newest_ = true;
};

} // namespace sbm_viewer
