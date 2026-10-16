// End conditions and check (spec/api/board_state.json).
#include <cstdint>

#include "arguments.hpp"
#include "board.hpp"
#include "sbm/board_state.h"

namespace sbm_js {

namespace {

template <sbm_status (*Function)(const sbm_board*, sbm_bool*), const char* What>
Napi::Value condition(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    return Napi::Boolean::New(env, query<sbm_bool>(env, Function, board, What) != 0);
}

Napi::Value is_repetition(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    const char* what = "Board.isRepetition";
    const auto count = to_c<std::int32_t>(info[0], what);
    return Napi::Boolean::New(
        env, query<sbm_bool>(env, sbm_board_is_repetition, board, what, count) != 0);
}

Napi::Value has_insufficient_material(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    const char* what = "Board.hasInsufficientMaterial";
    const auto color = to_c<sbm_color>(info[0], what);
    return Napi::Boolean::New(
        env, query<sbm_bool>(env, sbm_board_has_insufficient_material, board, what, color) != 0);
}

constexpr char kIsCheck[] = "Board.isCheck";
constexpr char kIsCheckmate[] = "Board.isCheckmate";
constexpr char kIsStalemate[] = "Board.isStalemate";
constexpr char kIsFiftyMoveRule[] = "Board.isFiftyMoveRule";
constexpr char kIsInsufficientMaterial[] = "Board.isInsufficientMaterial";
constexpr char kIsDraw[] = "Board.isDraw";
constexpr char kIsGameOver[] = "Board.isGameOver";

} // namespace

void add_board_state_methods(NativeBoard::Methods& methods) {
    NativeBoard::add<condition<sbm_board_is_check, kIsCheck>>(methods, "isCheck");
    NativeBoard::add<condition<sbm_board_is_checkmate, kIsCheckmate>>(methods, "isCheckmate");
    NativeBoard::add<condition<sbm_board_is_stalemate, kIsStalemate>>(methods, "isStalemate");
    NativeBoard::add<is_repetition>(methods, "isRepetition");
    NativeBoard::add<condition<sbm_board_is_fifty_move_rule, kIsFiftyMoveRule>>(
        methods, "isFiftyMoveRule");
    NativeBoard::add<condition<sbm_board_is_insufficient_material, kIsInsufficientMaterial>>(
        methods, "isInsufficientMaterial");
    NativeBoard::add<has_insufficient_material>(methods, "hasInsufficientMaterial");
    NativeBoard::add<condition<sbm_board_is_draw, kIsDraw>>(methods, "isDraw");
    NativeBoard::add<condition<sbm_board_is_game_over, kIsGameOver>>(methods, "isGameOver");
}

} // namespace sbm_js
