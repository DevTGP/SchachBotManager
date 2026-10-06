// Calls a C function with output parameters and stores its output as the JSON result.
#pragma once

#include <cstdint>
#include <string>
#include <vector>

#include "call.hpp"
#include "json_values.hpp"

namespace sbm_test {

// function(char* buffer, uint32_t size)
template <typename Function>
sbm_status text_output(Call& call, std::uint32_t size, Function&& function) {
    std::vector<char> buffer(size, '#');
    const sbm_status status = function(buffer.data(), size);
    if (status == SBM_OK) {
        call.result = std::string(buffer.data());
    }
    return status;
}

// function(sbm_move* out, uint32_t capacity, uint32_t* count); asks for the count first, as a
// binding does for move_history.
template <typename Function> sbm_status move_list_output(Call& call, Function&& function) {
    std::uint32_t count = 0;
    sbm_status status = function(nullptr, 0, &count);
    std::vector<sbm_move> moves;
    if (status == SBM_BUFFER_TOO_SMALL) {
        moves.resize(count);
        status = function(moves.data(), count, &count);
    }
    if (status == SBM_OK) {
        call.result = moves;
    }
    return status;
}

// function(T* out) for integer outputs.
template <typename T, typename Function>
sbm_status integer_output(Call& call, Function&& function) {
    T value{};
    const sbm_status status = function(&value);
    if (status == SBM_OK) {
        call.result = value;
    }
    return status;
}

template <typename Function> sbm_status bool_output(Call& call, Function&& function) {
    sbm_bool value = 0;
    const sbm_status status = function(&value);
    if (status == SBM_OK) {
        call.result = value != 0;
    }
    return status;
}

// Bitboard and u64 outputs.
template <typename Function> sbm_status hex_output(Call& call, Function&& function) {
    std::uint64_t value = 0;
    const sbm_status status = function(&value);
    if (status == SBM_OK) {
        call.result = hex_text(value);
    }
    return status;
}

} // namespace sbm_test
