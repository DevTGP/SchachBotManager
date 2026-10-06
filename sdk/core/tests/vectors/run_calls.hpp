// Runs the vectors of one file in the format of calls.schema.json.
#pragma once

#include <nlohmann/json.hpp>

#include "call.hpp"
#include "summary.hpp"

namespace sbm_test {

void run_call_vectors(const nlohmann::json& file, const Registry& registry, Summary& summary);

} // namespace sbm_test
