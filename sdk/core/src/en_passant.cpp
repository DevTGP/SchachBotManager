#include "en_passant.hpp"

#include "attacks.hpp"
#include "threats.hpp"

namespace sbm {

bool is_legal_en_passant(const Position& position, int from) {
    const Color us = position.side_to_move;
    const int target = position.en_passant;
    const int captured = us == kWhite ? target - 8 : target + 8;
    const Bitboard occupied =
        (position.occupied() ^ square_bb(from) ^ square_bb(captured)) | square_bb(target);
    const Bitboard attackers =
        attackers_of(position, position.king_square(us), opposite(us), occupied);
    return (attackers & ~square_bb(captured)) == 0;
}

int legal_en_passant_square(const Position& position) {
    if (position.en_passant == kNoSquare) {
        return kNoSquare;
    }
    const Color us = position.side_to_move;
    Bitboard capturers =
        pawn_attacks(opposite(us), position.en_passant) & position.pieces_of(us, kPawn);
    while (capturers != 0) {
        if (is_legal_en_passant(position, pop_lsb(capturers))) {
            return position.en_passant;
        }
    }
    return kNoSquare;
}

} // namespace sbm
