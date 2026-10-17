// JavaScript values as C types. Numbers that are no integers or do not fit raise
// InvalidArgumentError, like values the core rejects; values of the wrong type a TypeError.
#pragma once

#include <cmath>
#include <string>
#include <utility>

#include <napi.h>

#include "status.hpp"

namespace sbm_js {

inline double to_number(const Napi::Value& value, const char* what) {
    if (!value.IsNumber()) {
        throw Napi::TypeError::New(value.Env(), std::string(what) + ": expected a number");
    }
    return value.As<Napi::Number>().DoubleValue();
}

template <typename T> T to_c(const Napi::Value& value, const char* what) {
    const double number = to_number(value, what);
    // The bounds keep the cast to long long defined; every C type used here is far smaller.
    if (std::trunc(number) != number || number < -9.0e15 || number > 9.0e15 ||
        !std::in_range<T>(static_cast<long long>(number))) {
        throw_error(
            value.Env(), "InvalidArgumentError",
            std::string(what) + ": " + value.ToString().Utf8Value() + " is out of range");
    }
    return static_cast<T>(number);
}

inline std::string to_string(const Napi::Value& value, const char* what) {
    if (!value.IsString()) {
        throw Napi::TypeError::New(value.Env(), std::string(what) + ": expected a string");
    }
    return value.As<Napi::String>().Utf8Value();
}

// Strings with an embedded NUL would be cut short at the C boundary.
inline bool has_nul(const std::string& text) {
    return text.find('\0') != std::string::npos;
}

} // namespace sbm_js
