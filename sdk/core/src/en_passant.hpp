// En passant captures; the stored square may exist without a legal capture (E48).
#pragma once

#include "position.hpp"

namespace sbm {

// Whether the pawn of the side to move on `from` may capture en passant without leaving its
// king in check. The position must have an en passant square that this pawn attacks.
bool is_legal_en_passant(const Position& position, int from);

// The en passant square if a legal en passant capture exists, otherwise kNoSquare.
int legal_en_passant_square(const Position& position);

} // namespace sbm
