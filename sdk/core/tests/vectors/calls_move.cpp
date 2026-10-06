// Handlers for sbm/move.h. The bit operations of Move have no C function (E50).
#include "call.hpp"
#include "outputs.hpp"

namespace sbm_test {

void add_move_calls(Registry& registry) {
    registry["Move.parse"] = [](Call& call) {
        const std::string uci = call.string_arg(0);
        return integer_output<sbm_move>(
            call, [&](sbm_move* out) { return sbm_move_parse(uci.c_str(), out); });
    };
    registry["Move.uci"] = [](Call& call) {
        const auto move = call.vector.at("move").get<sbm_move>();
        return text_output(call, SBM_UCI_BUFFER_SIZE, [&](char* buffer, std::uint32_t size) {
            return sbm_move_uci(move, buffer, size);
        });
    };
}

} // namespace sbm_test
