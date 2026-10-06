#include "game.hpp"

#include "play.hpp"

namespace sbm {

void Game::make(Move move) {
    history_.push_back({position_, move});
    play_move(position_, move);
}

void Game::make_null() {
    history_.push_back({position_, kNullMove});
    play_null_move(position_);
}

void Game::undo() {
    position_ = history_.back().before;
    history_.pop_back();
}

} // namespace sbm
