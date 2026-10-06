// Handlers for sbm/board_state.h.
#include "call.hpp"
#include "outputs.hpp"

namespace sbm_test {

namespace {

using BoolFunction = sbm_status (*)(const sbm_board*, sbm_bool*);

Handler bool_query(BoolFunction function) {
    return [function](Call& call) {
        return bool_output(call, [&](sbm_bool* out) { return function(call.board, out); });
    };
}

} // namespace

void add_board_state_calls(Registry& registry) {
    registry["Board.is_check"] = bool_query(sbm_board_is_check);
    registry["Board.is_checkmate"] = bool_query(sbm_board_is_checkmate);
    registry["Board.is_stalemate"] = bool_query(sbm_board_is_stalemate);
    registry["Board.is_fifty_move_rule"] = bool_query(sbm_board_is_fifty_move_rule);
    registry["Board.is_insufficient_material"] = bool_query(sbm_board_is_insufficient_material);
    registry["Board.is_draw"] = bool_query(sbm_board_is_draw);
    registry["Board.is_game_over"] = bool_query(sbm_board_is_game_over);
    registry["Board.is_repetition"] = [](Call& call) {
        const auto count = call.integer_arg<std::int32_t>(0);
        return bool_output(
            call, [&](sbm_bool* out) { return sbm_board_is_repetition(call.board, count, out); });
    };
    registry["Board.has_insufficient_material"] = [](Call& call) {
        const auto color = call.integer_arg<sbm_color>(0);
        return bool_output(call, [&](sbm_bool* out) {
            return sbm_board_has_insufficient_material(call.board, color, out);
        });
    };
}

} // namespace sbm_test
