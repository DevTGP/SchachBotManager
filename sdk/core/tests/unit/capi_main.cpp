// Rules of the C interface (docs/komponenten/kern-c-schnittstelle.md) beyond the vectors.
#include "check.hpp"

void test_handles();
void test_buffers();

int main() {
    test_handles();
    test_buffers();
    return sbm_unit::report("sbm_capi_tests");
}
