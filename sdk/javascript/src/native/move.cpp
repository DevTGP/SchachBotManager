// moveParse and moveUci (spec/api/move.json); the TypeScript class Move wraps them.
#include "move.hpp"

#include <array>
#include <cstdint>

#include "arguments.hpp"
#include "sbm/move.h"
#include "status.hpp"
#include "values.hpp"

namespace sbm_js {

namespace {

Napi::Value parse(const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    const std::string uci = to_string(info[0], "Move.parse");
    if (has_nul(uci)) {
        throw_status(env, SBM_INVALID_UCI, "Move.parse");
    }
    sbm_move move = 0;
    const sbm_status status = sbm_move_parse(uci.c_str(), &move);
    if (status != SBM_OK) {
        throw_status(env, status, "Move.parse('" + uci + "')");
    }
    return Napi::Number::New(env, move);
}

Napi::Value uci(const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    const auto value = to_c<sbm_move>(info[0], "Move.uci");
    return read_text<SBM_UCI_BUFFER_SIZE>(
        env, [&](char* buffer, std::uint32_t size) { return sbm_move_uci(value, buffer, size); },
        "Move.uci");
}

} // namespace

std::string move_text(sbm_move value) {
    std::array<char, SBM_UCI_BUFFER_SIZE> text{};
    if (sbm_move_uci(value, text.data(), SBM_UCI_BUFFER_SIZE) != SBM_OK) {
        return std::to_string(value);
    }
    return std::string(text.data());
}

void bind_move(Napi::Env env, Napi::Object exports) {
    exports.Set("moveParse", Napi::Function::New(env, parse, "moveParse"));
    exports.Set("moveUci", Napi::Function::New(env, uci, "moveUci"));
}

} // namespace sbm_js
