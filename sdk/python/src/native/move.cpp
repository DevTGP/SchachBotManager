// Move (spec/api/move.json): the bit operations are computed here, parse and uci call the core.
#include "move.hpp"

#include <array>
#include <cstdint>
#include <string>

#include <nanobind/stl/string.h>

#include "arguments.hpp"
#include "sbm/move.h"
#include "status.hpp"
#include "text.hpp"

namespace nb = nanobind;
using namespace nb::literals;

namespace sbm_py {

namespace {

constexpr int kToShift = 6;
constexpr int kFlagShift = 12;

unsigned from_of(sbm_move value) {
    return value & 0x3Fu;
}

unsigned to_of(sbm_move value) {
    return (value >> kToShift) & 0x3Fu;
}

unsigned flags_of(sbm_move value) {
    return value >> kFlagShift;
}

bool unused_flags(unsigned flags) {
    return flags == 6 || flags == 7;
}

Move create(const nb::int_& from_square, const nb::int_& to_square, const nb::int_& flags) {
    const long long from = to_long(from_square, "Move: from_square");
    const long long to = to_long(to_square, "Move: to_square");
    const long long bits = to_long(flags, "Move: flags");
    if (from < 0 || from > 63 || to < 0 || to > 63) {
        raise_error("InvalidArgumentError", "Move: squares must be 0 to 63");
    }
    if (bits < 0 || bits > 15 || unused_flags(static_cast<unsigned>(bits))) {
        raise_error("InvalidArgumentError", "Move: flags must be 0 to 5 or 8 to 15");
    }
    return Move{static_cast<sbm_move>(from | (to << kToShift) | (bits << kFlagShift))};
}

Move from_value(const nb::int_& value) {
    const long long number = to_long(value, "Move.from_value");
    if (number < 0 || number > 0xFFFF) {
        raise_error("InvalidArgumentError", "Move.from_value: value must be 0 to 65535");
    }
    const auto move = static_cast<sbm_move>(number);
    if (unused_flags(flags_of(move))) {
        raise_error("InvalidArgumentError", "Move.from_value: flags 6 and 7 are unused");
    }
    return Move{move};
}

Move parse(const std::string& uci) {
    if (has_nul(uci)) {
        raise_status(SBM_INVALID_UCI, "Move.parse");
    }
    sbm_move move = 0;
    check(sbm_move_parse(uci.c_str(), &move), "Move.parse");
    return Move{move};
}

std::string uci(const Move& move) {
    return read_text<SBM_UCI_BUFFER_SIZE>(
        [&](char* buffer, std::uint32_t size) { return sbm_move_uci(move.value, buffer, size); },
        "Move.uci");
}

unsigned promotion(const Move& move) {
    const unsigned flags = flags_of(move.value);
    return flags >= SBM_FLAG_PROMOTION ? (flags & 3u) + 1 : SBM_NO_PIECE_TYPE;
}

bool is_capture(const Move& move) {
    const unsigned flags = flags_of(move.value);
    return flags == SBM_FLAG_CAPTURE || flags == SBM_FLAG_EN_PASSANT ||
           flags >= SBM_FLAG_PROMOTION_CAPTURE;
}

bool is_castling(const Move& move) {
    const unsigned flags = flags_of(move.value);
    return flags == SBM_FLAG_KING_CASTLE || flags == SBM_FLAG_QUEEN_CASTLE;
}

} // namespace

std::string move_repr(sbm_move value) {
    if (value == SBM_NULL_MOVE) {
        return "<Move NULL_MOVE>";
    }
    if (value == SBM_RESIGN) {
        return "<Move RESIGN>";
    }
    std::array<char, SBM_UCI_BUFFER_SIZE> text{};
    if (sbm_move_uci(value, text.data(), SBM_UCI_BUFFER_SIZE) != SBM_OK) {
        return "<Move " + std::to_string(value) + ">";
    }
    return "<Move " + std::string(text.data()) + " flags=" + std::to_string(flags_of(value)) + ">";
}

void bind_move(nb::module_& module) {
    nb::class_<Move> cls(module, "Move", "A move as 16-bit value: from-square, to-square, flags.");
    cls.def(
           "__init__",
           [](Move* self, const nb::int_& from_square, const nb::int_& to_square,
              const nb::int_& flags) { new (self) Move(create(from_square, to_square, flags)); },
           "from_square"_a, "to_square"_a, "flags"_a,
           "Builds a move from its parts without checking it against a position.")
        .def_static("from_value", &from_value, "value"_a, "Wraps a raw 16-bit value.")
        .def_static(
            "parse", &parse, "uci"_a,
            "Reads UCI notation without a board; flags only for promotions.")
        .def(
            "value", [](const Move& move) { return move.value; }, "The raw 16-bit value.")
        .def(
            "from_square", [](const Move& move) { return from_of(move.value); },
            "Start square (bits 0 to 5).")
        .def(
            "to_square", [](const Move& move) { return to_of(move.value); },
            "Target square (bits 6 to 11).")
        .def(
            "flags", [](const Move& move) { return flags_of(move.value); },
            "Flags (bits 12 to 15).")
        .def("promotion", &promotion, "Piece type of a promotion, otherwise NO_PIECE_TYPE.")
        .def(
            "is_promotion",
            [](const Move& move) { return flags_of(move.value) >= SBM_FLAG_PROMOTION; },
            "Flags 8 to 15.")
        .def("is_capture", &is_capture, "Flags 4, 5 and 12 to 15, including en passant.")
        .def("is_castling", &is_castling, "Flags 2 and 3.")
        .def(
            "is_en_passant",
            [](const Move& move) { return flags_of(move.value) == SBM_FLAG_EN_PASSANT; }, "Flag 5.")
        .def("uci", &uci, "UCI notation, e.g. e2e4 or e7e8q; castling as king move.")
        .def(
            "__eq__", [](const Move& a, const Move& b) { return a.value == b.value; },
            nb::is_operator())
        .def(
            "__ne__", [](const Move& a, const Move& b) { return a.value != b.value; },
            nb::is_operator())
        .def("__hash__", [](const Move& move) { return move.value; })
        .def("__repr__", [](const Move& move) { return move_repr(move.value); })
        .def("__copy__", [](nb::handle_t<Move> self) { return nb::borrow(self); })
        .def(
            "__deepcopy__", [](nb::handle_t<Move> self, nb::handle) { return nb::borrow(self); },
            "memo"_a);
    // Static properties instead of stored instances: a type holding its own instances forms a
    // cycle that outlives interpreter shutdown.
    cls.def_prop_ro_static("NULL_MOVE", [](nb::handle) { return Move{SBM_NULL_MOVE}; })
        .def_prop_ro_static("RESIGN", [](nb::handle) { return Move{SBM_RESIGN}; });
}

} // namespace sbm_py
