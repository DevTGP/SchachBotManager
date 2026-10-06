#include "json_values.hpp"

#include <algorithm>
#include <cstdio>
#include <vector>

namespace sbm_test {

std::string hex_text(std::uint64_t value) {
    char text[19];
    std::snprintf(text, sizeof text, "0x%016llx", static_cast<unsigned long long>(value));
    return text;
}

bool same_result(const nlohmann::json& actual, const nlohmann::json& expected, bool unordered) {
    if (!unordered || !actual.is_array() || !expected.is_array()) {
        return actual == expected;
    }
    std::vector<nlohmann::json> a(actual.begin(), actual.end());
    std::vector<nlohmann::json> b(expected.begin(), expected.end());
    std::sort(a.begin(), a.end());
    std::sort(b.begin(), b.end());
    return a == b;
}

} // namespace sbm_test
