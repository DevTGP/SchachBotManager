// Handlers for sbm/board_raw.h.
#include <array>

#include "call.hpp"
#include "outputs.hpp"

namespace sbm_test {

namespace {

sbm_status bitboards(Call& call) {
    std::array<sbm_bitboard, SBM_PIECE_COUNT> values{};
    const sbm_status status = sbm_board_bitboards(call.board, values.data());
    if (status == SBM_OK) {
        call.result = json::array();
        for (const sbm_bitboard value : values) {
            call.result.push_back(hex_text(value));
        }
    }
    return status;
}

sbm_status squares(Call& call) {
    std::array<sbm_piece, SBM_SQUARE_COUNT> values{};
    const sbm_status status = sbm_board_squares(call.board, values.data());
    if (status == SBM_OK) {
        call.result = values;
    }
    return status;
}

} // namespace

void add_board_raw_calls(Registry& registry) {
    registry["Board.bitboard"] = [](Call& call) {
        const auto color = call.integer_arg<sbm_color>(0);
        const auto type = call.integer_arg<sbm_piece_type>(1);
        return hex_output(call, [&](sbm_bitboard* out) {
            return sbm_board_bitboard(call.board, color, type, out);
        });
    };
    registry["Board.bitboards"] = bitboards;
    registry["Board.squares"] = squares;
    registry["Board.occupied"] = [](Call& call) {
        return hex_output(
            call, [&](sbm_bitboard* out) { return sbm_board_occupied(call.board, out); });
    };
    registry["Board.occupied_by"] = [](Call& call) {
        const auto color = call.integer_arg<sbm_color>(0);
        return hex_output(
            call, [&](sbm_bitboard* out) { return sbm_board_occupied_by(call.board, color, out); });
    };
    registry["Board.piece_count"] = [](Call& call) {
        const auto color = call.integer_arg<sbm_color>(0);
        const auto type = call.integer_arg<sbm_piece_type>(1);
        return integer_output<std::int32_t>(call, [&](std::int32_t* out) {
            return sbm_board_piece_count(call.board, color, type, out);
        });
    };
    registry["Board.attacks_from"] = [](Call& call) {
        const auto square = call.integer_arg<sbm_square>(0);
        return hex_output(call, [&](sbm_bitboard* out) {
            return sbm_board_attacks_from(call.board, square, out);
        });
    };
    registry["Board.attackers_of"] = [](Call& call) {
        const auto square = call.integer_arg<sbm_square>(0);
        const auto color = call.integer_arg<sbm_color>(1);
        return hex_output(call, [&](sbm_bitboard* out) {
            return sbm_board_attackers_of(call.board, square, color, out);
        });
    };
    registry["Board.is_attacked"] = [](Call& call) {
        const auto square = call.integer_arg<sbm_square>(0);
        const auto color = call.integer_arg<sbm_color>(1);
        return bool_output(call, [&](sbm_bool* out) {
            return sbm_board_is_attacked(call.board, square, color, out);
        });
    };
    registry["Board.checkers"] = [](Call& call) {
        return hex_output(
            call, [&](sbm_bitboard* out) { return sbm_board_checkers(call.board, out); });
    };
    registry["Board.pinned"] = [](Call& call) {
        const auto color = call.integer_arg<sbm_color>(0);
        return hex_output(
            call, [&](sbm_bitboard* out) { return sbm_board_pinned(call.board, color, out); });
    };
}

} // namespace sbm_test
