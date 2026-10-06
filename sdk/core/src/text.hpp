// Board.to_text: a diagram for debugging; the layout is not part of the API.
#pragma once

#include <string>

#include "position.hpp"

namespace sbm {

// Ranks 8 to 1 with FEN letters and dots, separated by spaces, then the FEN.
std::string write_text(const Position& position);

} // namespace sbm
