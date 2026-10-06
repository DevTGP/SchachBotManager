// Counts of passed, failed and skipped vectors; prints each failure.
#pragma once

#include <iostream>
#include <string_view>

namespace sbm_test {

struct Summary {
    int passed = 0;
    int failed = 0;
    int skipped = 0;

    void pass() {
        ++passed;
    }

    void fail(std::string_view id, std::string_view message) {
        ++failed;
        std::cout << "FAIL " << id << ": " << message << '\n';
    }

    void skip() {
        ++skipped;
    }
};

} // namespace sbm_test
