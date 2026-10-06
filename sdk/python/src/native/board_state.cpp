// End conditions (spec/api/board_state.json).
#include <cstdint>

#include "arguments.hpp"
#include "board.hpp"
#include "query.hpp"
#include "sbm/board_state.h"

namespace nb = nanobind;
using namespace nb::literals;

namespace sbm_py {

namespace {

using Condition = sbm_status (*)(const sbm_board*, sbm_bool*);

// Binds a condition without arguments as a method returning bool.
void condition(BoardClass& cls, const char* name, Condition function, const char* doc) {
    cls.def(
        name,
        [function, name](const Board& board) {
            return query<sbm_bool>(function, board, name) != 0;
        },
        doc);
}

} // namespace

void bind_board_state(BoardClass& cls) {
    condition(cls, "is_check", sbm_board_is_check, "Whether the side to move is in check.");
    condition(cls, "is_checkmate", sbm_board_is_checkmate, "Whether the side to move is mated.");
    condition(
        cls, "is_stalemate", sbm_board_is_stalemate,
        "Whether the side to move has no legal move and is not in check.");
    condition(
        cls, "is_fifty_move_rule", sbm_board_is_fifty_move_rule,
        "Whether the halfmove clock is at least 100 and the side to move is not mated.");
    condition(
        cls, "is_insufficient_material", sbm_board_is_insufficient_material,
        "Whether neither color can mate.");
    condition(
        cls, "is_draw", sbm_board_is_draw,
        "Stalemate, threefold repetition, fifty-move rule or insufficient material.");
    condition(cls, "is_game_over", sbm_board_is_game_over, "Checkmate or a draw.");
    cls.def(
           "is_repetition",
           [](const Board& board, const nb::int_& count) {
               constexpr const char* what = "Board.is_repetition";
               return query<sbm_bool>(
                          sbm_board_is_repetition, board, what, to_c<std::int32_t>(count, what)) !=
                      0;
           },
           "count"_a, "Whether the position occurred at least count times; 3 is threefold.")
        .def(
            "has_insufficient_material",
            [](const Board& board, const nb::int_& color) {
                constexpr const char* what = "Board.has_insufficient_material";
                return query<sbm_bool>(
                           sbm_board_has_insufficient_material, board, what,
                           to_c<sbm_color>(color, what)) != 0;
            },
            "color"_a, "Whether a color can no longer mate.");
}

} // namespace sbm_py
