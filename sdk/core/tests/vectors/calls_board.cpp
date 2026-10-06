// Handlers for sbm/board.h.
#include "board_setup.hpp"
#include "call.hpp"
#include "outputs.hpp"

namespace sbm_test {

namespace {

// Board.create, from_fen and copy return a board, encoded as its FEN.
template <typename Create> sbm_status created_board(Call& call, Create&& create) {
    sbm_board* created = nullptr;
    const sbm_status status = create(&created);
    if (status == SBM_OK) {
        const BoardPtr owner(created);
        call.result = board_fen(created);
    }
    return status;
}

} // namespace

void add_board_calls(Registry& registry) {
    registry["Board.create"] = [](Call& call) {
        return created_board(call, [](sbm_board** out) { return sbm_board_new(out); });
    };
    registry["Board.from_fen"] = [](Call& call) {
        const std::string fen = call.string_arg(0);
        return created_board(
            call, [&](sbm_board** out) { return sbm_board_from_fen(fen.c_str(), out); });
    };
    registry["Board.copy"] = [](Call& call) {
        return created_board(
            call, [&](sbm_board** out) { return sbm_board_copy(call.board, out); });
    };
    registry["Board.fen"] = [](Call& call) {
        return text_output(call, SBM_FEN_BUFFER_SIZE, [&](char* buffer, std::uint32_t size) {
            return sbm_board_fen(call.board, buffer, size);
        });
    };
    registry["Board.hash"] = [](Call& call) {
        return hex_output(
            call, [&](std::uint64_t* out) { return sbm_board_hash(call.board, out); });
    };
    registry["Board.move_history"] = [](Call& call) {
        return move_list_output(
            call, [&](sbm_move* out, std::uint32_t capacity, std::uint32_t* count) {
                return sbm_board_move_history(call.board, out, capacity, count);
            });
    };
    registry["Board.to_text"] = [](Call& call) {
        return text_output(call, SBM_TEXT_BUFFER_SIZE, [&](char* buffer, std::uint32_t size) {
            return sbm_board_to_text(call.board, buffer, size);
        });
    };
}

} // namespace sbm_test
