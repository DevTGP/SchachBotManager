// One position: pieces, side to move, castling rights, en passant square and move counters.
#pragma once

#include <array>
#include <cstdint>

#include "bitboard.hpp"
#include "piece.hpp"

namespace sbm {

// Castling bits of E35.
enum Castling : int {
    kWhiteKingside = 1,
    kWhiteQueenside = 2,
    kBlackKingside = 4,
    kBlackQueenside = 8,
};

struct Position {
    std::array<Bitboard, kPieceCount> pieces{};
    std::array<Bitboard, kColorCount> colors{};
    std::array<std::uint8_t, kSquareCount> squares;
    Color side_to_move = kWhite;
    int castling = 0;
    // Set after every double push and from the FEN, even without a legal en passant capture
    // (E48); see legal_en_passant_square.
    int en_passant = kNoSquare;
    int halfmove_clock = 0;
    int fullmove_number = 1;

    Position();

    Bitboard occupied() const {
        return colors[kWhite] | colors[kBlack];
    }

    Bitboard pieces_of(Color color, PieceType type) const {
        return pieces[make_piece(color, type)];
    }

    int piece_at(int square) const {
        return squares[square];
    }

    // The king square; a valid position has exactly one king per color.
    int king_square(Color color) const {
        return lsb(pieces_of(color, kKing));
    }

    void put(int piece, int square);
    void remove(int square);
};

Position start_position();

} // namespace sbm
