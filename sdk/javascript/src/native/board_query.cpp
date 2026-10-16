// Single properties of the position (spec/api/board_query.json).
#include <array>
#include <cstdint>

#include "arguments.hpp"
#include "board.hpp"
#include "sbm/board_query.h"

namespace sbm_js {

namespace {

template <typename T, sbm_status (*Function)(const sbm_board*, T*), const char* What>
Napi::Value number(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    return Napi::Number::New(env, query<T>(env, Function, board, What));
}

Napi::Value piece_at(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    const char* what = "Board.pieceAt";
    const auto square = to_c<sbm_square>(info[0], what);
    return Napi::Number::New(env, query<sbm_piece>(env, sbm_board_piece_at, board, what, square));
}

// Square and piece of each match in turn; src/board.ts builds the PlacedPiece records.
Napi::Value pieces(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    const char* what = "Board.pieces";
    const auto color = to_c<sbm_color>(info[0], what);
    const auto piece_type = to_c<sbm_piece_type>(info[1], what);
    std::array<sbm_square, SBM_SQUARE_COUNT> squares{};
    std::array<sbm_piece, SBM_SQUARE_COUNT> found{};
    std::uint32_t count = 0;
    check(
        env,
        sbm_board_pieces(
            board.get(), color, piece_type, squares.data(), found.data(), SBM_SQUARE_COUNT, &count),
        what);
    Napi::Uint8Array result = Napi::Uint8Array::New(env, count * 2);
    for (std::uint32_t i = 0; i < count; ++i) {
        result[i * 2] = squares[i];
        result[i * 2 + 1] = found[i];
    }
    return result;
}

Napi::Value king_square(NativeBoard& board, const Napi::CallbackInfo& info) {
    const Napi::Env env = info.Env();
    const char* what = "Board.kingSquare";
    const auto color = to_c<sbm_color>(info[0], what);
    return Napi::Number::New(
        env, query<sbm_square>(env, sbm_board_king_square, board, what, color));
}

constexpr char kSideToMove[] = "Board.sideToMove";
constexpr char kCastlingRights[] = "Board.castlingRights";
constexpr char kEnPassantSquare[] = "Board.enPassantSquare";
constexpr char kHalfmoveClock[] = "Board.halfmoveClock";
constexpr char kFullmoveNumber[] = "Board.fullmoveNumber";

} // namespace

void add_board_query_methods(NativeBoard::Methods& methods) {
    NativeBoard::add<piece_at>(methods, "pieceAt");
    NativeBoard::add<pieces>(methods, "pieces");
    NativeBoard::add<number<sbm_color, sbm_board_side_to_move, kSideToMove>>(methods, "sideToMove");
    NativeBoard::add<number<sbm_castling, sbm_board_castling_rights, kCastlingRights>>(
        methods, "castlingRights");
    NativeBoard::add<number<sbm_square, sbm_board_en_passant_square, kEnPassantSquare>>(
        methods, "enPassantSquare");
    NativeBoard::add<number<std::int32_t, sbm_board_halfmove_clock, kHalfmoveClock>>(
        methods, "halfmoveClock");
    NativeBoard::add<number<std::int32_t, sbm_board_fullmove_number, kFullmoveNumber>>(
        methods, "fullmoveNumber");
    NativeBoard::add<king_square>(methods, "kingSquare");
}

} // namespace sbm_js
