// Handlers for sbm/board_query.h.
#include "call.hpp"
#include "outputs.hpp"

namespace sbm_test {

void add_board_query_calls(Registry& registry) {
    registry["Board.piece_at"] = [](Call& call) {
        const auto square = call.integer_arg<sbm_square>(0);
        return integer_output<sbm_piece>(
            call, [&](sbm_piece* out) { return sbm_board_piece_at(call.board, square, out); });
    };
    registry["Board.side_to_move"] = [](Call& call) {
        return integer_output<sbm_color>(
            call, [&](sbm_color* out) { return sbm_board_side_to_move(call.board, out); });
    };
    registry["Board.castling_rights"] = [](Call& call) {
        return integer_output<sbm_castling>(
            call, [&](sbm_castling* out) { return sbm_board_castling_rights(call.board, out); });
    };
    registry["Board.en_passant_square"] = [](Call& call) {
        return integer_output<sbm_square>(
            call, [&](sbm_square* out) { return sbm_board_en_passant_square(call.board, out); });
    };
    registry["Board.halfmove_clock"] = [](Call& call) {
        return integer_output<std::int32_t>(
            call, [&](std::int32_t* out) { return sbm_board_halfmove_clock(call.board, out); });
    };
    registry["Board.fullmove_number"] = [](Call& call) {
        return integer_output<std::int32_t>(
            call, [&](std::int32_t* out) { return sbm_board_fullmove_number(call.board, out); });
    };
    registry["Board.king_square"] = [](Call& call) {
        const auto color = call.integer_arg<sbm_color>(0);
        return integer_output<sbm_square>(
            call, [&](sbm_square* out) { return sbm_board_king_square(call.board, color, out); });
    };
}

} // namespace sbm_test
