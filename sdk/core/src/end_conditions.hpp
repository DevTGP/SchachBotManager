// End conditions of spec/api/board_state.json; the referee ends a game on each of them.
#pragma once

#include "game.hpp"
#include "position.hpp"

namespace sbm {

bool is_check(const Position& position);
bool is_checkmate(const Position& position);
bool is_stalemate(const Position& position);
bool is_fifty_move_rule(const Position& position);
bool is_insufficient_material(const Position& position);
bool is_draw(const Game& game);
bool is_game_over(const Game& game);

} // namespace sbm
