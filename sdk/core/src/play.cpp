#include "play.hpp"

#include <array>
#include <cstdint>
#include <limits>

namespace sbm {

namespace {

// Castling rights lost when a piece moves from or to the square.
constexpr std::array<int, kSquareCount> make_castling_masks() {
    std::array<int, kSquareCount> masks{};
    masks[make_square(0, 0)] = kWhiteQueenside;
    masks[make_square(4, 0)] = kWhiteKingside | kWhiteQueenside;
    masks[make_square(7, 0)] = kWhiteKingside;
    masks[make_square(0, 7)] = kBlackQueenside;
    masks[make_square(4, 7)] = kBlackKingside | kBlackQueenside;
    masks[make_square(7, 7)] = kBlackKingside;
    return masks;
}

constexpr auto kCastlingMasks = make_castling_masks();

// Counters stop at the largest value a FEN may hold instead of overflowing.
int saturating_increment(int value) {
    return value < std::numeric_limits<std::int32_t>::max() ? value + 1 : value;
}

void advance_counters(Position& position, bool reset_halfmove_clock) {
    position.halfmove_clock =
        reset_halfmove_clock ? 0 : saturating_increment(position.halfmove_clock);
    if (position.side_to_move == kBlack) {
        position.fullmove_number = saturating_increment(position.fullmove_number);
    }
    position.side_to_move = opposite(position.side_to_move);
}

void move_rook_for_castling(Position& position, int king_to, int flags) {
    const int rank = rank_of(king_to);
    const int rook_from = make_square(flags == kKingCastle ? 7 : 0, rank);
    const int rook_to = make_square(flags == kKingCastle ? 5 : 3, rank);
    const int rook = position.piece_at(rook_from);
    position.remove(rook_from);
    position.put(rook, rook_to);
}

} // namespace

void play_move(Position& position, Move move) {
    const Color us = position.side_to_move;
    const int from = from_square(move);
    const int to = to_square(move);
    const int flags = move_flags(move);
    const int piece = position.piece_at(from);
    const bool pawn_move = type_of(piece) == kPawn;

    if (flags == kEnPassant) {
        position.remove(us == kWhite ? to - 8 : to + 8);
    } else if (is_capture(move)) {
        position.remove(to);
    }
    position.remove(from);
    position.put(is_promotion(move) ? make_piece(us, promotion_type(move)) : piece, to);
    if (is_castling(move)) {
        move_rook_for_castling(position, to, flags);
    }

    position.castling &= ~(kCastlingMasks[from] | kCastlingMasks[to]);
    position.en_passant = flags == kDoublePawnPush ? (from + to) / 2 : kNoSquare;
    advance_counters(position, pawn_move || is_capture(move));
}

void play_null_move(Position& position) {
    position.en_passant = kNoSquare;
    advance_counters(position, false);
}

} // namespace sbm
