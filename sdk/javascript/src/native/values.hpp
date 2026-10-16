// Results of the C interface as JavaScript values: move lists, 64-bit values and text.
#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string>

#include <napi.h>

#include "sbm/types.h"
#include "status.hpp"

namespace sbm_js {

inline Napi::Uint16Array move_array(Napi::Env env, const sbm_move* moves, std::uint32_t count) {
    Napi::Uint16Array result = Napi::Uint16Array::New(env, count);
    if (count > 0) {
        std::memcpy(result.Data(), moves, count * sizeof(sbm_move));
    }
    return result;
}

// The low and high half of each value, for the functions with the suffix 32 (E204).
inline Napi::Uint32Array halves(Napi::Env env, const std::uint64_t* values, std::size_t count) {
    Napi::Uint32Array result = Napi::Uint32Array::New(env, count * 2);
    for (std::size_t i = 0; i < count; ++i) {
        result[i * 2] = static_cast<std::uint32_t>(values[i]);
        result[i * 2 + 1] = static_cast<std::uint32_t>(values[i] >> 32);
    }
    return result;
}

// `call` receives the buffer and its size and returns the status of the C function.
template <std::size_t Size, typename Call>
Napi::String read_text(Napi::Env env, Call&& call, const char* what) {
    std::array<char, Size> buffer{};
    check(env, call(buffer.data(), static_cast<std::uint32_t>(Size)), what);
    return Napi::String::New(env, buffer.data());
}

} // namespace sbm_js
