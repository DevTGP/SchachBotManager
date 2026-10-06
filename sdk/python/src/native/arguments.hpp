// Python integers as C integer types. Values that do not fit raise InvalidArgumentError, like
// values the core rejects, instead of a TypeError or OverflowError.
#pragma once

#include <string>
#include <utility>

#include <nanobind/nanobind.h>

#include "status.hpp"

namespace sbm_py {

inline long long to_long(const nanobind::int_& value, const char* what) {
    int overflow = 0;
    const long long number = PyLong_AsLongLongAndOverflow(value.ptr(), &overflow);
    if (number == -1 && PyErr_Occurred() != nullptr) {
        throw nanobind::python_error();
    }
    if (overflow != 0) {
        raise_error("InvalidArgumentError", std::string(what) + ": value out of range");
    }
    return number;
}

template <typename T> T to_c(const nanobind::int_& value, const char* what) {
    const long long number = to_long(value, what);
    if (!std::in_range<T>(number)) {
        raise_error(
            "InvalidArgumentError",
            std::string(what) + ": " + std::to_string(number) + " is out of range");
    }
    return static_cast<T>(number);
}

} // namespace sbm_py
