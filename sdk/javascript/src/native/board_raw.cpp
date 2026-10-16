// Raw access for fast evaluations (spec/api/board_raw.json). Every bitboard comes as bigint and,
// with the suffix 32, as a Uint32Array with the low and high half (E204).
#include <array>
#include <cstdint>

#include "arguments.hpp"
#include "board.hpp"
#include "sbm/board_raw.h"
#include "values.hpp"

namespace sbm_js {

namespace {

template <bool Halves> Napi::Value bits(Napi::Env env, std::uint64_t value) {
    if constexpr (Halves) {
        return halves(env, &value, 1);
    } else {
        return Napi::BigInt::New(env, value);
    }
}

template <bool Halves> Napi::Value bitboard(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    const char* what = "Board.bitboard";
    const auto color = to_c<sbm_color>(info[0], what);
    const auto piece_type = to_c<sbm_piece_type>(info[1], what);
    return bits<Halves>(
        env, query<sbm_bitboard>(env, sbm_board_bitboard, board, what, color, piece_type));
}

Napi::Value bitboards(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    Napi::BigUint64Array result = Napi::BigUint64Array::New(env, SBM_PIECE_COUNT);
    check(env, sbm_board_bitboards(board.get(), result.Data()), "Board.bitboards");
    return result;
}

Napi::Value bitboards32(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    std::array<sbm_bitboard, SBM_PIECE_COUNT> values{};
    check(env, sbm_board_bitboards(board.get(), values.data()), "Board.bitboards32");
    return halves(env, values.data(), values.size());
}

Napi::Value squares(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    Napi::Uint8Array result = Napi::Uint8Array::New(env, SBM_SQUARE_COUNT);
    check(env, sbm_board_squares(board.get(), result.Data()), "Board.squares");
    return result;
}

template <bool Halves> Napi::Value occupied(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    return bits<Halves>(env, query<sbm_bitboard>(env, sbm_board_occupied, board, "Board.occupied"));
}

template <bool Halves> Napi::Value occupied_by(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    const char* what = "Board.occupiedBy";
    const auto color = to_c<sbm_color>(info[0], what);
    return bits<Halves>(env, query<sbm_bitboard>(env, sbm_board_occupied_by, board, what, color));
}

Napi::Value piece_count(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    const char* what = "Board.pieceCount";
    const auto color = to_c<sbm_color>(info[0], what);
    const auto piece_type = to_c<sbm_piece_type>(info[1], what);
    return Napi::Number::New(
        env, query<std::int32_t>(env, sbm_board_piece_count, board, what, color, piece_type));
}

template <bool Halves>
Napi::Value attacks_from(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    const char* what = "Board.attacksFrom";
    const auto square = to_c<sbm_square>(info[0], what);
    return bits<Halves>(env, query<sbm_bitboard>(env, sbm_board_attacks_from, board, what, square));
}

template <bool Halves>
Napi::Value attackers_of(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    const char* what = "Board.attackersOf";
    const auto square = to_c<sbm_square>(info[0], what);
    const auto color = to_c<sbm_color>(info[1], what);
    return bits<Halves>(
        env, query<sbm_bitboard>(env, sbm_board_attackers_of, board, what, square, color));
}

Napi::Value is_attacked(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    const char* what = "Board.isAttacked";
    const auto square = to_c<sbm_square>(info[0], what);
    const auto color = to_c<sbm_color>(info[1], what);
    return Napi::Boolean::New(
        env, query<sbm_bool>(env, sbm_board_is_attacked, board, what, square, color) != 0);
}

template <bool Halves> Napi::Value checkers(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    return bits<Halves>(env, query<sbm_bitboard>(env, sbm_board_checkers, board, "Board.checkers"));
}

template <bool Halves> Napi::Value pinned(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    const char* what = "Board.pinned";
    const auto color = to_c<sbm_color>(info[0], what);
    return bits<Halves>(env, query<sbm_bitboard>(env, sbm_board_pinned, board, what, color));
}

} // namespace

void add_board_raw_methods(NativeBoard::Methods& methods) {
    NativeBoard::add<bitboard<false>>(methods, "bitboard");
    NativeBoard::add<bitboard<true>>(methods, "bitboard32");
    NativeBoard::add<bitboards>(methods, "bitboards");
    NativeBoard::add<bitboards32>(methods, "bitboards32");
    NativeBoard::add<squares>(methods, "squares");
    NativeBoard::add<occupied<false>>(methods, "occupied");
    NativeBoard::add<occupied<true>>(methods, "occupied32");
    NativeBoard::add<occupied_by<false>>(methods, "occupiedBy");
    NativeBoard::add<occupied_by<true>>(methods, "occupiedBy32");
    NativeBoard::add<piece_count>(methods, "pieceCount");
    NativeBoard::add<attacks_from<false>>(methods, "attacksFrom");
    NativeBoard::add<attacks_from<true>>(methods, "attacksFrom32");
    NativeBoard::add<attackers_of<false>>(methods, "attackersOf");
    NativeBoard::add<attackers_of<true>>(methods, "attackersOf32");
    NativeBoard::add<is_attacked>(methods, "isAttacked");
    NativeBoard::add<checkers<false>>(methods, "checkers");
    NativeBoard::add<checkers<true>>(methods, "checkers32");
    NativeBoard::add<pinned<false>>(methods, "pinned");
    NativeBoard::add<pinned<true>>(methods, "pinned32");
}

} // namespace sbm_js
