// Handlers for sbm/board_moves.h.
#include "call.hpp"
#include "outputs.hpp"

namespace sbm_test {

void add_board_moves_calls(Registry& registry) {
    registry["Board.legal_moves"] = [](Call& call) {
        return move_list_output(
            call, [&](sbm_move* out, std::uint32_t capacity, std::uint32_t* count) {
                return sbm_board_legal_moves(call.board, out, capacity, count);
            });
    };
    registry["Board.legal_captures"] = [](Call& call) {
        return move_list_output(
            call, [&](sbm_move* out, std::uint32_t capacity, std::uint32_t* count) {
                return sbm_board_legal_captures(call.board, out, capacity, count);
            });
    };
    registry["Board.is_legal"] = [](Call& call) {
        const auto move = call.integer_arg<sbm_move>(0);
        return bool_output(
            call, [&](sbm_bool* out) { return sbm_board_is_legal(call.board, move, out); });
    };
    registry["Board.parse_move"] = [](Call& call) {
        const std::string uci = call.string_arg(0);
        return integer_output<sbm_move>(call, [&](sbm_move* out) {
            return sbm_board_parse_move(call.board, uci.c_str(), out);
        });
    };
    registry["Board.san"] = [](Call& call) {
        const auto move = call.integer_arg<sbm_move>(0);
        return text_output(call, SBM_SAN_BUFFER_SIZE, [&](char* buffer, std::uint32_t size) {
            return sbm_board_san(call.board, move, buffer, size);
        });
    };
    registry["Board.make_move"] = [](Call& call) {
        return sbm_board_make_move(call.board, call.integer_arg<sbm_move>(0));
    };
    registry["Board.undo_move"] = [](Call& call) {
        return sbm_board_undo_move(call.board);
    };
    registry["Board.make_null_move"] = [](Call& call) {
        return sbm_board_make_null_move(call.board);
    };
    registry["Board.undo_null_move"] = [](Call& call) {
        return sbm_board_undo_null_move(call.board);
    };
}

} // namespace sbm_test
