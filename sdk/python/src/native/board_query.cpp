// Single properties of the position (spec/api/board_query.json).
#include <array>
#include <cstdint>
#include <optional>

#include <nanobind/stl/optional.h>

#include "arguments.hpp"
#include "board.hpp"
#include "query.hpp"
#include "sbm/board_query.h"

namespace nb = nanobind;
using namespace nb::literals;

namespace sbm_py {

namespace {

// PlacedPiece is a dataclass of sbm.records, looked up on demand like the errors.
nb::list pieces(
    const Board& board, const std::optional<nb::int_>& color,
    const std::optional<nb::int_>& piece_type) {
    const char* what = "Board.pieces";
    const auto color_code = color ? to_c<sbm_color>(*color, what) : sbm_color{SBM_NO_COLOR};
    const auto type_code =
        piece_type ? to_c<sbm_piece_type>(*piece_type, what) : sbm_piece_type{SBM_NO_PIECE_TYPE};
    std::array<sbm_square, SBM_SQUARE_COUNT> squares{};
    std::array<sbm_piece, SBM_SQUARE_COUNT> found{};
    std::uint32_t count = 0;
    check(
        sbm_board_pieces(
            board.get(), color_code, type_code, squares.data(), found.data(), SBM_SQUARE_COUNT,
            &count),
        what);
    const nb::object placed_piece = nb::module_::import_("sbm.records").attr("PlacedPiece");
    nb::list result;
    for (std::uint32_t i = 0; i < count; ++i) {
        result.append(placed_piece(squares[i], found[i]));
    }
    return result;
}

} // namespace

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
            "pieces", &pieces, "color"_a = nb::none(), "piece_type"_a = nb::none(),
            nb::sig("def pieces(self, color: int | None = None, piece_type: int | None = None) "
                    "-> list[sbm.records.PlacedPiece]"),
            "The pieces with their squares from a1 to h8, of one color or both (None) and of one "
            "type or all (None).")
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
