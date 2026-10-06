// One call vector at run time: the board it runs on, its arguments and the returned value.
#pragma once

#include <cstddef>
#include <functional>
#include <map>
#include <stdexcept>
#include <string>
#include <utility>

#include <nlohmann/json.hpp>

#include "sbm/sbm.h"

namespace sbm_test {

using nlohmann::json;

struct Call {
    const json& vector;
    sbm_board* board; // the board of the vector, or nullptr if it has none
    json result;      // set by the handler on SBM_OK, encoded as in calls.schema.json

    const json& arg(std::size_t index) const {
        return vector.at("args").at(index);
    }

    std::string string_arg(std::size_t index) const {
        return arg(index).get<std::string>();
    }

    // The argument as the C type; vectors with values outside its range are not callable.
    template <typename T> T integer_arg(std::size_t index) const {
        const auto value = arg(index).get<long long>();
        if (!std::in_range<T>(value)) {
            throw std::runtime_error("argument does not fit the C type: " + std::to_string(value));
        }
        return static_cast<T>(value);
    }
};

// Calls the C function of one API function and returns its status.
using Handler = std::function<sbm_status(Call&)>;
using Registry = std::map<std::string, Handler, std::less<>>;

void add_board_calls(Registry& registry);
void add_board_moves_calls(Registry& registry);
void add_board_query_calls(Registry& registry);
void add_board_raw_calls(Registry& registry);
void add_board_state_calls(Registry& registry);
void add_move_calls(Registry& registry);

} // namespace sbm_test
