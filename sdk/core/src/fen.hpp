// Reading and writing FEN with the rules of Board.from_fen and Board.fen (spec/api/board.json).
#pragma once

#include <optional>
#include <string>
#include <string_view>

#include "position.hpp"

namespace sbm {

// The position, keeping the en passant square as given; nothing if syntax or position are
// invalid.
std::optional<Position> parse_fen(std::string_view fen);

// Names the en passant square only if a legal en passant capture exists (E48).
std::string write_fen(const Position& position);

} // namespace sbm
