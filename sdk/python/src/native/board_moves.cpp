// Generating, checking, making and taking back moves (spec/api/board_moves.json).
#include <array>
#include <cstdint>
#include <string>

#include <nanobind/stl/string.h>

#include "board.hpp"
#include "move.hpp"
#include "move_list.hpp"
#include "query.hpp"
#include "sbm/board_moves.h"
#include "status.hpp"
#include "text.hpp"

namespace nb = nanobind;
using namespace nb::literals;

namespace sbm_py {

namespace {

using MoveGenerator = sbm_status (*)(const sbm_board*, sbm_move*, std::uint32_t, std::uint32_t*);

MoveList generate(const Board& board, MoveGenerator generator, const char* what) {
    std::array<sbm_move, SBM_MAX_MOVES> moves{};
    std::uint32_t count = 0;
    check(generator(board.get(), moves.data(), SBM_MAX_MOVES, &count), what);
    return move_list(moves.data(), count);
}

Move parse_move(const Board& board, const std::string& uci) {
    if (has_nul(uci)) {
        raise_status(SBM_INVALID_UCI, "Board.parse_move");
    }
    sbm_move move = 0;
    const sbm_status status = sbm_board_parse_move(board.get(), uci.c_str(), &move);
    if (status != SBM_OK) {
        raise_status(status, "Board.parse_move('" + uci + "')");
    }
    return Move{move};
}

std::string san(const Board& board, const Move& move) {
    std::array<char, SBM_SAN_BUFFER_SIZE> text{};
    const sbm_status status =
        sbm_board_san(board.get(), move.value, text.data(), SBM_SAN_BUFFER_SIZE);
    if (status != SBM_OK) {
        raise_status(status, "Board.san(" + move_repr(move.value) + ")");
    }
    return std::string(text.data());
}

void make_move(const Board& board, const Move& move) {
    const sbm_status status = sbm_board_make_move(board.get(), move.value);
    if (status != SBM_OK) {
        raise_status(status, "Board.make_move(" + move_repr(move.value) + ")");
    }
}

} // namespace

void bind_board_moves(BoardClass& cls) {
    cls.def(
           "legal_moves",
           [](const Board& board) {
               return generate(board, sbm_board_legal_moves, "Board.legal_moves");
           },
           "All legal moves of the side to move.")
        .def(
            "legal_captures",
            [](const Board& board) {
                return generate(board, sbm_board_legal_captures, "Board.legal_captures");
            },
            "The legal moves that capture, including en passant and capturing promotions.")
        .def(
            "is_legal",
            [](const Board& board, const Move& move) {
                return query<sbm_bool>(sbm_board_is_legal, board, "Board.is_legal", move.value) !=
                       0;
            },
            "move"_a, "Whether the move is legal; compares from, to and promotion.")
        .def("parse_move", &parse_move, "uci"_a, "The legal move in UCI notation, with all flags.")
        .def("san", &san, "move"_a, "Standard algebraic notation of a legal move, e.g. Nf3.")
        .def("make_move", &make_move, "move"_a, "Makes a legal move.")
        .def(
            "undo_move",
            [](const Board& board) { check(sbm_board_undo_move(board.get()), "Board.undo_move"); },
            "Takes back the last move.")
        .def(
            "make_null_move",
            [](const Board& board) {
                check(sbm_board_make_null_move(board.get()), "Board.make_null_move");
            },
            "Passes the turn; not possible in check.")
        .def(
            "undo_null_move",
            [](const Board& board) {
                check(sbm_board_undo_null_move(board.get()), "Board.undo_null_move");
            },
            "Takes back the last null move.");
}

} // namespace sbm_py
