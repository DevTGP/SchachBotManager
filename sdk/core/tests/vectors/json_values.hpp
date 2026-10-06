// Encoding of values in call vectors that JSON has no type for (calls.schema.json).
#pragma once

#include <cstdint>
#include <string>

#include <nlohmann/json.hpp>

namespace sbm_test {

// u64 and Bitboard: 0x plus 16 lower-case hex digits.
std::string hex_text(std::uint64_t value);

// Compares a result with the expected value; with unordered, arrays compare as multisets.
bool same_result(const nlohmann::json& actual, const nlohmann::json& expected, bool unordered);

} // namespace sbm_test
