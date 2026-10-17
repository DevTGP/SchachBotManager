// Move.parse and Move.uci call the core; the bit operations live in src/move.ts.
#pragma once

#include <string>

#include <napi.h>

#include "sbm/types.h"

namespace sbm_js {

// UCI notation for messages, or the raw value where the move has none.
std::string move_text(sbm_move value);

void bind_move(Napi::Env env, Napi::Object exports);

} // namespace sbm_js
