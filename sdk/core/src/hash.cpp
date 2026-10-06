#include "hash.hpp"

#include "attacks.hpp"
#include "polyglot_keys.hpp"

namespace sbm {

namespace {

std::uint64_t piece_keys(const Position& position) {
    std::uint64_t hash = 0;
    Bitboard occupied = position.occupied();
    while (occupied != 0) {
        const int square = pop_lsb(occupied);
        const int piece = position.piece_at(square);
        const int white = color_of(piece) == kWhite ? 1 : 0;
        hash ^= kPolyglotKeys[64 * (2 * type_of(piece) + white) + square];
    }
    return hash;
}

std::uint64_t castling_keys(int castling) {
    std::uint64_t hash = 0;
    for (int index = 0; index < 4; ++index) {
        if ((castling & (1 << index)) != 0) {
            hash ^= kPolyglotKeys[kPolyglotCastlingOffset + index];
        }
    }
    return hash;
}

std::uint64_t en_passant_key(const Position& position) {
    if (position.en_passant == kNoSquare) {
        return 0;
    }
    // Pawns of the side to move that attack the square stand next to the pushed pawn.
    const Color us = position.side_to_move;
    const Bitboard capturers =
        pawn_attacks(opposite(us), position.en_passant) & position.pieces_of(us, kPawn);
    if (capturers == 0) {
        return 0;
    }
    return kPolyglotKeys[kPolyglotEnPassantOffset + file_of(position.en_passant)];
}

} // namespace

std::uint64_t polyglot_hash(const Position& position) {
    std::uint64_t hash =
        piece_keys(position) ^ castling_keys(position.castling) ^ en_passant_key(position);
    if (position.side_to_move == kWhite) {
        hash ^= kPolyglotKeys[kPolyglotWhiteToMoveIndex];
    }
    return hash;
}

} // namespace sbm
