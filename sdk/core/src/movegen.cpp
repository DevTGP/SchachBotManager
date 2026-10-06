#include "movegen.hpp"

#include "attacks.hpp"
#include "en_passant.hpp"
#include "threats.hpp"

namespace sbm {

namespace {

class Generator {
public:
    Generator(const Position& position, MoveList& list)
        : position_(position), list_(list), us_(position.side_to_move), them_(opposite(us_)),
          own_(position.colors[us_]), enemy_(position.colors[them_]),
          occupied_(position.occupied()), king_(position.king_square(us_)),
          pinned_(pinned(position, us_)), targets_(~own_) {}

    void generate() {
        king_moves();
        const Bitboard checking = checkers(position_);
        if (popcount(checking) > 1) {
            return;
        }
        if (checking != 0) {
            targets_ = checking | between(king_, lsb(checking));
        } else {
            castling_moves();
        }
        pawn_moves();
        for (const PieceType type : {kKnight, kBishop, kRook, kQueen}) {
            piece_moves(type);
        }
    }

private:
    const Position& position_;
    MoveList& list_;
    Color us_;
    Color them_;
    Bitboard own_;
    Bitboard enemy_;
    Bitboard occupied_;
    int king_;
    Bitboard pinned_;
    // Squares a piece other than the king may move to: all but own pieces, or while in check
    // the checker and the squares between it and the king.
    Bitboard targets_;

    Bitboard allowed(int from) const {
        if ((pinned_ & square_bb(from)) != 0) {
            return targets_ & line_through(king_, from);
        }
        return targets_;
    }

    void add(int from, int to) {
        list_.add(encode_move(from, to, (enemy_ & square_bb(to)) != 0 ? kCapture : kQuiet));
    }

    void add_pawn(int from, int to, bool capture) {
        if (rank_of(to) != 0 && rank_of(to) != 7) {
            list_.add(encode_move(from, to, capture ? kCapture : kQuiet));
            return;
        }
        const int base = capture ? kPromotionCapture : kPromotion;
        for (int piece = 0; piece < 4; ++piece) {
            list_.add(encode_move(from, to, base + piece));
        }
    }

    void king_moves() {
        const Bitboard without_king = occupied_ ^ square_bb(king_);
        Bitboard destinations = king_attacks(king_) & ~own_;
        while (destinations != 0) {
            const int to = pop_lsb(destinations);
            if (attackers_of(position_, to, them_, without_king) == 0) {
                add(king_, to);
            }
        }
    }

    // Castling rights imply king and rook on their start squares (Board.from_fen, make_move).
    void castling_side(int right, int rook_file, int king_file, int flags) {
        if ((position_.castling & right) == 0) {
            return;
        }
        const int rook = make_square(rook_file, rank_of(king_));
        const int destination = make_square(king_file, rank_of(king_));
        if ((between(king_, rook) & occupied_) != 0) {
            return;
        }
        Bitboard path = between(king_, destination) | square_bb(destination);
        while (path != 0) {
            if (is_attacked(position_, pop_lsb(path), them_)) {
                return;
            }
        }
        list_.add(encode_move(king_, destination, flags));
    }

    void castling_moves() {
        const bool white = us_ == kWhite;
        castling_side(white ? kWhiteKingside : kBlackKingside, 7, 6, kKingCastle);
        castling_side(white ? kWhiteQueenside : kBlackQueenside, 0, 2, kQueenCastle);
    }

    void pawn_moves() {
        const int forward = us_ == kWhite ? 8 : -8;
        const int start_rank = us_ == kWhite ? 1 : 6;
        Bitboard pawns = position_.pieces_of(us_, kPawn);
        while (pawns != 0) {
            const int from = pop_lsb(pawns);
            const Bitboard destinations = allowed(from);
            const int one = from + forward;
            if ((occupied_ & square_bb(one)) == 0) {
                if ((destinations & square_bb(one)) != 0) {
                    add_pawn(from, one, false);
                }
                const int two = one + forward;
                if (rank_of(from) == start_rank && (occupied_ & square_bb(two)) == 0 &&
                    (destinations & square_bb(two)) != 0) {
                    list_.add(encode_move(from, two, kDoublePawnPush));
                }
            }
            Bitboard captures = pawn_attacks(us_, from) & enemy_ & destinations;
            while (captures != 0) {
                add_pawn(from, pop_lsb(captures), true);
            }
            en_passant(from);
        }
    }

    // Checked separately: the capture removes a pawn from a square other than the destination.
    void en_passant(int from) {
        const int target = position_.en_passant;
        if (target != kNoSquare && (pawn_attacks(us_, from) & square_bb(target)) != 0 &&
            is_legal_en_passant(position_, from)) {
            list_.add(encode_move(from, target, kEnPassant));
        }
    }

    void piece_moves(PieceType type) {
        Bitboard pieces = position_.pieces_of(us_, type);
        while (pieces != 0) {
            const int from = pop_lsb(pieces);
            Bitboard destinations = piece_attacks(type, us_, from, occupied_) & allowed(from);
            while (destinations != 0) {
                add(from, pop_lsb(destinations));
            }
        }
    }
};

} // namespace

void generate_legal_moves(const Position& position, MoveList& list) {
    Generator(position, list).generate();
}

void generate_legal_captures(const Position& position, MoveList& list) {
    MoveList all;
    generate_legal_moves(position, all);
    for (const Move move : all) {
        if (is_capture(move)) {
            list.add(move);
        }
    }
}

std::optional<Move> find_legal_move(const Position& position, Move move) {
    if (!has_valid_flags(move)) {
        return std::nullopt;
    }
    MoveList legal;
    generate_legal_moves(position, legal);
    for (const Move candidate : legal) {
        if (same_move(candidate, move)) {
            return candidate;
        }
    }
    return std::nullopt;
}

} // namespace sbm
