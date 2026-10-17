// State of the addon per Node environment: the board class and the error classes of the SDK.
#pragma once

#include <napi.h>

namespace sbm_js {

struct AddonData {
    Napi::FunctionReference board_class;
    // Object with the error classes of src/errors.ts, set once by setErrorClasses.
    Napi::ObjectReference errors;
};

inline AddonData& addon_data(Napi::Env env) {
    return *env.GetInstanceData<AddonData>();
}

} // namespace sbm_js
