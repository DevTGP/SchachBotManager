// Board.create, from_fen, fen, copy, hash, move_history and to_text (spec/api/board.json).
#include <cstdint>
#include <string>
#include <vector>

#include <nanobind/stl/string.h>

#include "board.hpp"
#include "move_list.hpp"
#include "query.hpp"
#include "status.hpp"
#include "text.hpp"

namespace nb = nanobind;
using namespace nb::literals;

namespace sbm_py {

namespace {

Board start_position() {
    sbm_board* handle = nullptr;
    check(sbm_board_new(&handle), "Board");
    return Board(handle);
}

Board from_fen(const std::string& fen) {
    if (has_nul(fen)) {
        raise_status(SBM_INVALID_FEN, "Board.from_fen");
    }
    sbm_board* handle = nullptr;
    check(sbm_board_from_fen(fen.c_str(), &handle), "Board.from_fen");
    return Board(handle);
}

Board copy(const Board& board) {
    sbm_board* handle = nullptr;
    check(sbm_board_copy(board.get(), &handle), "Board.copy");
    return Board(handle);
}

std::string fen(const Board& board) {
    return read_text<SBM_FEN_BUFFER_SIZE>(
        [&](char* buffer, std::uint32_t size) { return sbm_board_fen(board.get(), buffer, size); },
        "Board.fen");
}

std::string to_text(const Board& board) {
    return read_text<SBM_TEXT_BUFFER_SIZE>(
        [&](char* buffer, std::uint32_t size) {
            return sbm_board_to_text(board.get(), buffer, size);
        },
        "Board.to_text");
}

MoveList move_history(const Board& board) {
    std::uint32_t count = 0;
    const sbm_status status = sbm_board_move_history(board.get(), nullptr, 0, &count);
    if (status != SBM_BUFFER_TOO_SMALL) {
        check(status, "Board.move_history");
    }
    std::vector<sbm_move> moves(count);
    check(sbm_board_move_history(board.get(), moves.data(), count, &count), "Board.move_history");
    return move_list(moves.data(), count);
}

} // namespace

void bind_board(BoardClass& cls) {
    cls.def(
           "__init__", [](Board* self) { new (self) Board(start_position()); },
           "A board in the standard start position.")
        .def_static("from_fen", &from_fen, "fen"_a, "A board in the position of a FEN string.")
        .def("fen", &fen, "The position as FEN.")
        .def("copy", &copy, "An independent board including the move history.")
        .def(
            "hash",
            [](const Board& board) {
                return query<std::uint64_t>(sbm_board_hash, board, "Board.hash");
            },
            "Polyglot hash of the position.")
        .def("move_history", &move_history, "Moves made since the board was created, oldest first.")
        .def("to_text", &to_text, "The board as readable text for debugging.")
        .def("__str__", &to_text)
        .def("__repr__", [](const Board& board) { return "Board.from_fen('" + fen(board) + "')"; })
        .def("__copy__", &copy)
        .def("__deepcopy__", [](const Board& board, nb::handle) { return copy(board); }, "memo"_a);
}

} // namespace sbm_py
