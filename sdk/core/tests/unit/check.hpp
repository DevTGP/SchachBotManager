// Minimal assertion for the unit tests: CHECK records a failure and goes on.
#pragma once

#include <iostream>

namespace sbm_unit {

inline int& failure_count() {
    static int count = 0;
    return count;
}

inline void check(bool condition, const char* expression, const char* file, int line) {
    if (!condition) {
        ++failure_count();
        std::cout << file << ':' << line << ": CHECK(" << expression << ") failed\n";
    }
}

// Exit code of a test program: 0 if no check failed.
inline int report(const char* program) {
    std::cout << program << ": " << failure_count() << " failed checks\n";
    return failure_count() == 0 ? 0 : 1;
}

} // namespace sbm_unit

#define CHECK(expression) ::sbm_unit::check((expression), #expression, __FILE__, __LINE__)
