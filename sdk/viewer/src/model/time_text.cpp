#include "time_text.hpp"

#include <algorithm>
#include <cstdio>

namespace sbm_viewer {

std::string clock_text(int64_t ms) {
    ms = std::max<int64_t>(ms, 0);
    char buffer[32];
    if (ms < 10'000) {
        std::snprintf(
            buffer, sizeof buffer, "0:%02lld.%lld", static_cast<long long>(ms / 1000),
            static_cast<long long>(ms % 1000 / 100));
        return buffer;
    }
    const long long seconds = ms / 1000;
    if (seconds < 3600) {
        std::snprintf(buffer, sizeof buffer, "%lld:%02lld", seconds / 60, seconds % 60);
    } else {
        std::snprintf(
            buffer, sizeof buffer, "%lld:%02lld:%02lld", seconds / 3600, seconds / 60 % 60,
            seconds % 60);
    }
    return buffer;
}

std::string duration_text(int64_t ms) {
    ms = std::max<int64_t>(ms, 0);
    char buffer[32];
    if (ms < 1000) {
        std::snprintf(buffer, sizeof buffer, "%lld ms", static_cast<long long>(ms));
    } else if (ms < 60'000) {
        std::snprintf(
            buffer, sizeof buffer, "%lld.%lld s", static_cast<long long>(ms / 1000),
            static_cast<long long>(ms % 1000 / 100));
    } else {
        const long long seconds = ms / 1000;
        std::snprintf(buffer, sizeof buffer, "%lld:%02lld", seconds / 60, seconds % 60);
    }
    return buffer;
}

} // namespace sbm_viewer
