// Move generation and making moves (spec/api/board_moves.json); moves travel as 16-bit values.
#include <array>
#include <cstdint>
#include <string>

#include "arguments.hpp"
#include "board.hpp"
#include "move.hpp"
#include "sbm/board_moves.h"
#include "values.hpp"

namespace sbm_js {

namespace {

template <typename Generate>
Napi::Value
generate(const Napi::Env env, const NativeBoard& board, Generate generate_moves, const char* what) {
    std::array<sbm_move, SBM_MAX_MOVES> moves{};
    std::uint32_t count = 0;
    check(env, generate_moves(board.get(), moves.data(), SBM_MAX_MOVES, &count), what);
    return move_array(env, moves.data(), count);
}

Napi::Value legal_moves(NativeBoard& board, const Napi::CallbackInfo& info) {
    return generate(info.Env(), board, sbm_board_legal_moves, "Board.legalMoves");
}

Napi::Value legal_captures(NativeBoard& board, const Napi::CallbackInfo& info) {
    return generate(info.Env(), board, sbm_board_legal_captures, "Board.legalCaptures");
}

Napi::Value all_moves_from(NativeBoard& board, const Napi::CallbackInfo& info) {
    const char* what = "Board.allMovesFrom";
    const auto square = to_c<sbm_square>(info[0], what);
    return generate(
        info.Env(), board,
        [square](
            const sbm_board* handle, sbm_move* out, std::uint32_t capacity, std::uint32_t* count) {
            return sbm_board_all_moves_from(handle, square, out, capacity, count);
        },
        what);
}

Napi::Value is_legal(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    const char* what = "Board.isLegal";
    const auto move = to_c<sbm_move>(info[0], what);
    return Napi::Boolean::New(
        env, query<sbm_bool>(env, sbm_board_is_legal, board, what, move) != 0);
}

Napi::Value parse_move(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    const std::string uci = to_string(info[0], "Board.parseMove");
    if (has_nul(uci)) {
        throw_status(env, SBM_INVALID_UCI, "Board.parseMove");
    }
    sbm_move move = 0;
    const sbm_status status = sbm_board_parse_move(board.get(), uci.c_str(), &move);
    if (status != SBM_OK) {
        throw_status(env, status, "Board.parseMove('" + uci + "')");
    }
    return Napi::Number::New(env, move);
}

Napi::Value san(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    const auto move = to_c<sbm_move>(info[0], "Board.san");
    std::array<char, SBM_SAN_BUFFER_SIZE> text{};
    const sbm_status status = sbm_board_san(board.get(), move, text.data(), SBM_SAN_BUFFER_SIZE);
    if (status != SBM_OK) {
        throw_status(env, status, "Board.san(" + move_text(move) + ")");
    }
    return Napi::String::New(env, text.data());
}

Napi::Value make_move(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    const auto move = to_c<sbm_move>(info[0], "Board.makeMove");
    const sbm_status status = sbm_board_make_move(board.get(), move);
    if (status != SBM_OK) {
        throw_status(env, status, "Board.makeMove(" + move_text(move) + ")");
    }
    return env.Undefined();
}

template <sbm_status (*Function)(sbm_board*), const char* What>
Napi::Value change(NativeBoard& board, const Napi::CallbackInfo& info) {
    check(info.Env(), Function(board.get()), What);
    return info.Env().Undefined();
}

constexpr char kUndoMove[] = "Board.undoMove";
constexpr char kMakeNullMove[] = "Board.makeNullMove";
constexpr char kUndoNullMove[] = "Board.undoNullMove";

} // namespace

void add_board_moves_methods(NativeBoard::Methods& methods) {
    NativeBoard::add<legal_moves>(methods, "legalMoves");
    NativeBoard::add<legal_captures>(methods, "legalCaptures");
    NativeBoard::add<all_moves_from>(methods, "allMovesFrom");
    NativeBoard::add<is_legal>(methods, "isLegal");
    NativeBoard::add<parse_move>(methods, "parseMove");
    NativeBoard::add<san>(methods, "san");
    NativeBoard::add<make_move>(methods, "makeMove");
    NativeBoard::add<change<sbm_board_undo_move, kUndoMove>>(methods, "undoMove");
    NativeBoard::add<change<sbm_board_make_null_move, kMakeNullMove>>(methods, "makeNullMove");
    NativeBoard::add<change<sbm_board_undo_null_move, kUndoNullMove>>(methods, "undoNullMove");
}

} // namespace sbm_js
