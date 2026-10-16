// Board.create, fromFen, fen, copy, hash, moveHistory and toText (spec/api/board.json).
#include "board.hpp"

#include <cstdint>
#include <string>
#include <vector>

#include "addon.hpp"
#include "arguments.hpp"
#include "values.hpp"

namespace sbm_js {

namespace {

sbm_board* open_board(const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    sbm_board* handle = nullptr;
    if (info.Length() == 0 || info[0].IsUndefined()) {
        check(env, sbm_board_new(&handle), "Board");
    } else if (info[0].IsExternal()) {
        handle = info[0].As<Napi::External<sbm_board>>().Data();
    } else {
        const std::string fen = to_string(info[0], "Board.fromFen");
        if (has_nul(fen)) {
            throw_status(env, SBM_INVALID_FEN, "Board.fromFen");
        }
        check(env, sbm_board_from_fen(fen.c_str(), &handle), "Board.fromFen");
    }
    return handle;
}

Napi::Value fen(NativeBoard& board, const Napi::CallbackInfo& info) {
    return read_text<SBM_FEN_BUFFER_SIZE>(
        info.Env(),
        [&](char* buffer, std::uint32_t size) { return sbm_board_fen(board.get(), buffer, size); },
        "Board.fen");
}

Napi::Value to_text(NativeBoard& board, const Napi::CallbackInfo& info) {
    return read_text<SBM_TEXT_BUFFER_SIZE>(
        info.Env(),
        [&](char* buffer, std::uint32_t size) {
            return sbm_board_to_text(board.get(), buffer, size);
        },
        "Board.toText");
}

Napi::Value copy(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    sbm_board* handle = nullptr;
    check(env, sbm_board_copy(board.get(), &handle), "Board.copy");
    // The new object adopts the handle in its constructor.
    return addon_data(env).board_class.New({Napi::External<sbm_board>::New(env, handle)});
}

Napi::Value hash(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    return Napi::BigInt::New(env, query<std::uint64_t>(env, sbm_board_hash, board, "Board.hash"));
}

Napi::Value hash32(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    const auto value = query<std::uint64_t>(env, sbm_board_hash, board, "Board.hash32");
    return halves(env, &value, 1);
}

Napi::Value move_history(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    std::uint32_t count = 0;
    const sbm_status status = sbm_board_move_history(board.get(), nullptr, 0, &count);
    if (status != SBM_BUFFER_TOO_SMALL) {
        check(env, status, "Board.moveHistory");
    }
    std::vector<sbm_move> moves(count);
    check(
        env, sbm_board_move_history(board.get(), moves.data(), count, &count), "Board.moveHistory");
    return move_array(env, moves.data(), count);
}

} // namespace

NativeBoard::NativeBoard(const Napi::CallbackInfo& info)
    : Napi::ObjectWrap<NativeBoard>(info), handle_(open_board(info)) {}

Napi::Function NativeBoard::define(Napi::Env env) {
    Methods methods;
    add_board_methods(methods);
    add_board_moves_methods(methods);
    add_board_query_methods(methods);
    add_board_raw_methods(methods);
    add_board_state_methods(methods);
    return DefineClass(env, "NativeBoard", methods);
}

void add_board_methods(NativeBoard::Methods& methods) {
    NativeBoard::add<fen>(methods, "fen");
    NativeBoard::add<to_text>(methods, "toText");
    NativeBoard::add<copy>(methods, "copy");
    NativeBoard::add<hash>(methods, "hash");
    NativeBoard::add<hash32>(methods, "hash32");
    NativeBoard::add<move_history>(methods, "moveHistory");
}

} // namespace sbm_js
