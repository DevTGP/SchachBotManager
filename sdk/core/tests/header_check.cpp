// Compiles the public headers as C++20, the language the core and the C++ SDK use.
#include "sbm/sbm.h"

#include <type_traits>

static_assert(
    std::is_same_v<decltype(&sbm_board_new), sbm_status (*)(sbm_board**)>,
    "declarations have C linkage and the expected signature");

int main() {
    return SBM_OK;
}
