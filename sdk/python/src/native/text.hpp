// Reads text output of the C interface into a fixed buffer of the documented size.
#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>

#include "status.hpp"

namespace sbm_py {

// `call` receives the buffer and its size and returns the status of the C function.
template <std::size_t Size, typename Call> std::string read_text(Call&& call, const char* what) {
    std::array<char, Size> buffer{};
    check(call(buffer.data(), static_cast<std::uint32_t>(Size)), what);
    return std::string(buffer.data());
}

// Strings with an embedded NUL would be cut short at the C boundary.
inline bool has_nul(const std::string& text) {
    return text.find('\0') != std::string::npos;
}

} // namespace sbm_py
