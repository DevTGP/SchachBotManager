#include "navigation.hpp"

#include <algorithm>

namespace sbm_viewer {

int Navigation::shown(int count) const {
    return pinned_ ? std::clamp(*pinned_, 0, count) : count;
}

void Navigation::go_to(int ply, int count) {
    if (ply >= count) {
        pinned_.reset();
    } else {
        pinned_ = std::max(ply, 0);
    }
}

void Navigation::step(int delta, int count) {
    go_to(shown(count) + delta, count);
}

void Navigation::first(int count) {
    go_to(0, count);
}

void Navigation::last() {
    pinned_.reset();
}

void Navigation::select_game(int index, int game_count) {
    if (game_count <= 0) {
        return;
    }
    game_ = std::clamp(index, 0, game_count - 1);
    follow_newest_ = game_ == game_count - 1;
    pinned_.reset();
}

void Navigation::games_changed(int game_count) {
    if (follow_newest_ && game_count > 0 && game_ != game_count - 1) {
        game_ = game_count - 1;
        pinned_.reset();
    }
}

} // namespace sbm_viewer
