// Unit tests of internal engine modules.
#include "check.hpp"

void test_attacks();

int main() {
    test_attacks();
    return sbm_unit::report("sbm_engine_tests");
}
