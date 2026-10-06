// Raw access as bitboards and arrays (spec/api/board_raw.json).
#include <array>
#include <cstdint>

#include "arguments.hpp"
#include "board.hpp"
#include "query.hpp"
#include "sbm/board_raw.h"
#include "status.hpp"

namespace nb = nanobind;
using namespace nb::literals;

namespace sbm_py {

namespace {

using IntList = nb::typed<nb::list, nb::int_>;

template <typename T, std::size_t Size> IntList to_list(const std::array<T, Size>& values) {
    IntList result;
    for (const T value : values) {
        result.append(nb::int_(value));
    }
    return result;
}

IntList bitboards(const Board& board) {
    std::array<sbm_bitboard, SBM_PIECE_COUNT> values{};
    check(sbm_board_bitboards(board.get(), values.data()), "Board.bitboards");
    return to_list(values);
}

IntList squares(const Board& board) {
    std::array<sbm_piece, SBM_SQUARE_COUNT> values{};
    check(sbm_board_squares(board.get(), values.data()), "Board.squares");
    return to_list(values);
}

sbm_color color_arg(const nb::int_& color, const char* what) {
    return to_c<sbm_color>(color, what);
}

sbm_square square_arg(const nb::int_& square, const char* what) {
    return to_c<sbm_square>(square, what);
}

} // namespace

void bind_board_raw(BoardClass& cls) {
    cls.def(
           "bitboard",
           [](const Board& board, const nb::int_& color, const nb::int_& piece_type) {
               constexpr const char* what = "Board.bitboard";
               return query<sbm_bitboard>(
                   sbm_board_bitboard, board, what, color_arg(color, what),
                   to_c<sbm_piece_type>(piece_type, what));
           },
           "color"_a, "piece_type"_a, "Squares of the pieces of one color and type.")
        .def("bitboards", &bitboards, "All 12 piece bitboards, indexed by piece.")
        .def("squares", &squares, "The piece on each of the 64 squares, NO_PIECE if empty.")
        .def(
            "occupied",
            [](const Board& board) {
                return query<sbm_bitboard>(sbm_board_occupied, board, "Board.occupied");
            },
            "Squares with any piece.")
        .def(
            "occupied_by",
            [](const Board& board, const nb::int_& color) {
                constexpr const char* what = "Board.occupied_by";
                return query<sbm_bitboard>(
                    sbm_board_occupied_by, board, what, color_arg(color, what));
            },
            "color"_a, "Squares with a piece of one color.")
        .def(
            "piece_count",
            [](const Board& board, const nb::int_& color, const nb::int_& piece_type) {
                constexpr const char* what = "Board.piece_count";
                return query<std::int32_t>(
                    sbm_board_piece_count, board, what, color_arg(color, what),
                    to_c<sbm_piece_type>(piece_type, what));
            },
            "color"_a, "piece_type"_a, "Number of pieces of one color and type.")
        .def(
            "attacks_from",
            [](const Board& board, const nb::int_& square) {
                constexpr const char* what = "Board.attacks_from";
                return query<sbm_bitboard>(
                    sbm_board_attacks_from, board, what, square_arg(square, what));
            },
            "square"_a, "Squares attacked by the piece on a square; 0 if empty.")
        .def(
            "attackers_of",
            [](const Board& board, const nb::int_& square, const nb::int_& color) {
                constexpr const char* what = "Board.attackers_of";
                return query<sbm_bitboard>(
                    sbm_board_attackers_of, board, what, square_arg(square, what),
                    color_arg(color, what));
            },
            "square"_a, "color"_a, "Pieces of a color that attack a square.")
        .def(
            "is_attacked",
            [](const Board& board, const nb::int_& square, const nb::int_& color) {
                constexpr const char* what = "Board.is_attacked";
                return query<sbm_bool>(
                           sbm_board_is_attacked, board, what, square_arg(square, what),
                           color_arg(color, what)) != 0;
            },
            "square"_a, "color"_a, "Whether a color attacks a square.")
        .def(
            "checkers",
            [](const Board& board) {
                return query<sbm_bitboard>(sbm_board_checkers, board, "Board.checkers");
            },
            "Pieces giving check to the side to move.")
        .def(
            "pinned",
            [](const Board& board, const nb::int_& color) {
                constexpr const char* what = "Board.pinned";
                return query<sbm_bitboard>(sbm_board_pinned, board, what, color_arg(color, what));
            },
            "color"_a, "Pieces of a color pinned to their own king.");
}

} // namespace sbm_py
