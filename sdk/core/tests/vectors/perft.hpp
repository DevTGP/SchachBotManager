// Runs the vectors of one file in the format of perft.schema.json through the C interface.
#pragma once

#include <nlohmann/json.hpp>

#include "summary.hpp"

namespace sbm_test {

// Vectors marked slow run only if slow is set; otherwise they count as skipped.
void run_perft_vectors(const nlohmann::json& file, bool slow, Summary& summary);

} // namespace sbm_test
