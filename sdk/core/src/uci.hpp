// Moves in UCI notation (Move.parse, Move.uci).
#pragma once

#include <optional>
#include <string>
#include <string_view>

#include "move.hpp"

namespace sbm {

// [a-h][1-8][a-h][1-8][nbrq]? with flags 8 to 11 for a promotion and 0 otherwise.
std::optional<Move> parse_uci(std::string_view text);

// Nothing for NULL_MOVE, RESIGN and values with flags 6 or 7.
std::optional<std::string> write_uci(Move move);

} // namespace sbm
