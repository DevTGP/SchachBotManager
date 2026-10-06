#include "san.hpp"

#include "movegen.hpp"
#include "notation.hpp"
#include "play.hpp"
#include "threats.hpp"

namespace sbm {

namespace {

// From-squares of other pieces of the same type with a legal move to the same square.
Bitboard rivals(const Position& position, Move move) {
    const int from = from_square(move);
    const int piece = position.piece_at(from);
    MoveList legal;
    generate_legal_moves(position, legal);
    Bitboard result = 0;
    for (const Move other : legal) {
        const int other_from = from_square(other);
        if (other_from != from && to_square(other) == to_square(move) &&
            position.piece_at(other_from) == piece) {
            result |= square_bb(other_from);
        }
    }
    return result;
}

void append_disambiguation(std::string& san, const Position& position, Move move) {
    const Bitboard others = rivals(position, move);
    if (others == 0) {
        return;
    }
    const int from = from_square(move);
    const bool same_file = (others & file_bb(file_of(from))) != 0;
    const bool same_rank = (others & rank_bb(rank_of(from))) != 0;
    if (same_rank || !same_file) {
        san += file_letter(from);
    }
    if (same_file) {
        san += rank_digit(from);
    }
}

void append_suffix(std::string& san, const Position& position, Move move) {
    Position after = position;
    play_move(after, move);
    if (checkers(after) == 0) {
        return;
    }
    MoveList replies;
    generate_legal_moves(after, replies);
    san += replies.size == 0 ? '#' : '+';
}

} // namespace

std::string write_san(const Position& position, Move move) {
    std::string san;
    const int flags = move_flags(move);
    if (flags == kKingCastle || flags == kQueenCastle) {
        san = flags == kKingCastle ? "O-O" : "O-O-O";
        append_suffix(san, position, move);
        return san;
    }
    const int from = from_square(move);
    const PieceType type = type_of(position.piece_at(from));
    if (type == kPawn) {
        if (is_capture(move)) {
            san += file_letter(from);
        }
    } else {
        san += kPieceLetters[type];
        append_disambiguation(san, position, move);
    }
    if (is_capture(move)) {
        san += 'x';
    }
    append_square(san, to_square(move));
    if (is_promotion(move)) {
        san += '=';
        san += kPieceLetters[promotion_type(move)];
    }
    append_suffix(san, position, move);
    return san;
}

} // namespace sbm
