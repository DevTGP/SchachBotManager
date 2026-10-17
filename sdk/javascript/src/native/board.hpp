// NativeBoard: owns one board handle of the core, freed with the JavaScript object (E22). It
// returns plain values only; the class Board of src/board.ts turns them into the API (E221).
#pragma once

#include <memory>
#include <vector>

#include <napi.h>

#include "sbm/board.h"
#include "status.hpp"

namespace sbm_js {

struct BoardFree {
    void operator()(sbm_board* board) const noexcept {
        sbm_board_free(board);
    }
};

class NativeBoard : public Napi::ObjectWrap<NativeBoard> {
public:
    // A method as a free function, so each module of spec/api/ keeps its own file.
    using Function = Napi::Value (*)(NativeBoard&, const Napi::CallbackInfo&);
    using Methods = std::vector<Napi::ClassPropertyDescriptor<NativeBoard>>;

    // No argument: start position; a string: a FEN; an External: a handle to adopt.
    explicit NativeBoard(const Napi::CallbackInfo& info);

    sbm_board* get() const noexcept {
        return handle_.get();
    }

    template <Function F> static void add(Methods& methods, const char* name) {
        methods.push_back(InstanceMethod(name, &NativeBoard::call<F>));
    }

    static Napi::Function define(Napi::Env env);

private:
    template <Function F> Napi::Value call(const Napi::CallbackInfo& info) {
        return F(*this, info);
    }

    std::unique_ptr<sbm_board, BoardFree> handle_;
};

// function(handle, args..., &out); `what` names the API function for error messages.
template <typename T, typename Function, typename... Args>
T query(
    Napi::Env env, Function function, const NativeBoard& board, const char* what, Args... args) {
    T out{};
    check(env, function(board.get(), args..., &out), what);
    return out;
}

// One function per module of spec/api/ that adds its methods.
void add_board_methods(NativeBoard::Methods& methods);
void add_board_moves_methods(NativeBoard::Methods& methods);
void add_board_query_methods(NativeBoard::Methods& methods);
void add_board_raw_methods(NativeBoard::Methods& methods);
void add_board_state_methods(NativeBoard::Methods& methods);

} // namespace sbm_js
