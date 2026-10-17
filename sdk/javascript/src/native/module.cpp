// Entry of the addon sbm.node (E221): checks the ABI of the core and exports NativeBoard, the
// move functions and the version. src/native.ts loads it and hands over the error classes.
#include <napi.h>

#include "addon.hpp"
#include "board.hpp"
#include "move.hpp"
#include "sbm/sbm.h"

namespace sbm_js {

namespace {

Napi::Value set_error_classes(const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    if (!info[0].IsObject()) {
        throw Napi::TypeError::New(env, "setErrorClasses: expected an object");
    }
    addon_data(env).errors = Napi::Persistent(info[0].As<Napi::Object>());
    return env.Undefined();
}

} // namespace

Napi::Object init(Napi::Env env, Napi::Object exports) {
    if (sbm_abi_version() != SBM_ABI_VERSION) {
        throw Napi::Error::New(env, "sbm.node: the core has a different ABI version");
    }
    auto* data = new AddonData();
    env.SetInstanceData(data);
    const Napi::Function board_class = NativeBoard::define(env);
    data->board_class = Napi::Persistent(board_class);
    exports.Set("NativeBoard", board_class);
    bind_move(env, exports);
    exports.Set("version", Napi::String::New(env, sbm_version()));
    exports.Set("setErrorClasses", Napi::Function::New(env, set_error_classes, "setErrorClasses"));
    return exports;
}

} // namespace sbm_js

// The macro builds names from its second argument, so it takes an unqualified function.
static Napi::Object init_addon(Napi::Env env, Napi::Object exports) {
    return sbm_js::init(env, exports);
}

NODE_API_MODULE(sbm, init_addon)
