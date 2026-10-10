// Move list rows and search information as text.
#pragma once

#include <cstdint>
#include <string>
#include <vector>

#include "messages.hpp"
#include "position.hpp"

namespace sbm_viewer {

// One row of the move list; a half-move of 0 means the cell stays empty.
struct MoveRow {
    int number = 1;
    int white_ply = 0;
    int black_ply = 0;
};

// Rows for `ply_count` half-moves from a start position with the given move number and side.
std::vector<MoveRow> move_rows(int ply_count, int first_number, bool black_starts);

// "+0.25", "-1.50", "#3", "#-2"; empty without a score.
std::string score_text(const SearchInfo& info);
// "950", "12.3k", "4.5M".
std::string nodes_text(int64_t nodes);
// Principal variation in SAN from `from`, stopping at the first move that is not legal.
std::string pv_text(const Position& from, const std::vector<std::string>& pv);

} // namespace sbm_viewer
