// Single properties of the position (spec/api/board_query.json).
#include <cstdint>

#include "arguments.hpp"
#include "board.hpp"
#include "query.hpp"
#include "sbm/board_query.h"

namespace nb = nanobind;
using namespace nb::literals;

namespace sbm_py {

void bind_board_query(BoardClass& cls) {
    cls.def(
           "piece_at",
           [](const Board& board, const nb::int_& square) {
               return query<sbm_piece>(
                   sbm_board_piece_at, board, "Board.piece_at",
                   to_c<sbm_square>(square, "Board.piece_at"));
           },
           "square"_a, "The piece on a square, or NO_PIECE.")
        .def(
            "side_to_move",
            [](const Board& board) {
                return query<sbm_color>(sbm_board_side_to_move, board, "Board.side_to_move");
            },
            "WHITE or BLACK.")
        .def(
            "castling_rights",
            [](const Board& board) {
                return query<sbm_castling>(
                    sbm_board_castling_rights, board, "Board.castling_rights");
            },
            "Castling rights as bit mask.")
        .def(
            "en_passant_square",
            [](const Board& board) {
                return query<sbm_square>(
                    sbm_board_en_passant_square, board, "Board.en_passant_square");
            },
            "The en passant square if capturing there is legal, otherwise NO_SQUARE.")
        .def(
            "halfmove_clock",
            [](const Board& board) {
                return query<std::int32_t>(sbm_board_halfmove_clock, board, "Board.halfmove_clock");
            },
            "Half moves since the last capture or pawn move.")
        .def(
            "fullmove_number",
            [](const Board& board) {
                return query<std::int32_t>(
                    sbm_board_fullmove_number, board, "Board.fullmove_number");
            },
            "Move number, starting at 1 and increased after Black's move.")
        .def(
            "king_square",
            [](const Board& board, const nb::int_& color) {
                return query<sbm_square>(
                    sbm_board_king_square, board, "Board.king_square",
                    to_c<sbm_color>(color, "Board.king_square"));
            },
            "color"_a, "Square of the king of a color.");
}

} // namespace sbm_py
