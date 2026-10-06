#include "end_conditions.hpp"

#include "material.hpp"
#include "movegen.hpp"
#include "repetition.hpp"
#include "threats.hpp"

namespace sbm {

namespace {

constexpr int kFiftyMoveHalfmoves = 100;
constexpr int kThreefold = 3;

bool has_legal_move(const Position& position) {
    MoveList list;
    generate_legal_moves(position, list);
    return list.size > 0;
}

} // namespace

bool is_check(const Position& position) {
    return checkers(position) != 0;
}

bool is_checkmate(const Position& position) {
    return is_check(position) && !has_legal_move(position);
}

bool is_stalemate(const Position& position) {
    return !is_check(position) && !has_legal_move(position);
}

bool is_fifty_move_rule(const Position& position) {
    return position.halfmove_clock >= kFiftyMoveHalfmoves && !is_checkmate(position);
}

bool is_insufficient_material(const Position& position) {
    return has_insufficient_material(position, kWhite) &&
           has_insufficient_material(position, kBlack);
}

bool is_draw(const Game& game) {
    const Position& position = game.position();
    return is_stalemate(position) || repetition_count(game) >= kThreefold ||
           is_fifty_move_rule(position) || is_insufficient_material(position);
}

bool is_game_over(const Game& game) {
    return is_checkmate(game.position()) || is_draw(game);
}

} // namespace sbm
