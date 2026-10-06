#include "threats.hpp"

#include "attacks.hpp"

namespace sbm {

Bitboard attackers_of(const Position& position, int square, Color by, Bitboard occupied) {
    const Bitboard queens = position.pieces_of(by, kQueen);
    return (pawn_attacks(opposite(by), square) & position.pieces_of(by, kPawn)) |
           (knight_attacks(square) & position.pieces_of(by, kKnight)) |
           (king_attacks(square) & position.pieces_of(by, kKing)) |
           (bishop_attacks(square, occupied) & (position.pieces_of(by, kBishop) | queens)) |
           (rook_attacks(square, occupied) & (position.pieces_of(by, kRook) | queens));
}

Bitboard attackers_of(const Position& position, int square, Color by) {
    return attackers_of(position, square, by, position.occupied());
}

bool is_attacked(const Position& position, int square, Color by) {
    return attackers_of(position, square, by) != 0;
}

Bitboard attacks_from(const Position& position, int square) {
    const int piece = position.piece_at(square);
    if (piece == kNoPiece) {
        return 0;
    }
    return piece_attacks(type_of(piece), color_of(piece), square, position.occupied());
}

Bitboard checkers(const Position& position) {
    const Color us = position.side_to_move;
    return attackers_of(position, position.king_square(us), opposite(us));
}

Bitboard pinned(const Position& position, Color color) {
    const Color them = opposite(color);
    const int king = position.king_square(color);
    const Bitboard queens = position.pieces_of(them, kQueen);
    Bitboard snipers = (rook_attacks(king, 0) & (position.pieces_of(them, kRook) | queens)) |
                       (bishop_attacks(king, 0) & (position.pieces_of(them, kBishop) | queens));
    Bitboard result = 0;
    while (snipers != 0) {
        const Bitboard blockers = between(king, pop_lsb(snipers)) & position.occupied();
        if (popcount(blockers) == 1) {
            result |= blockers & position.colors[color];
        }
    }
    return result;
}

} // namespace sbm
