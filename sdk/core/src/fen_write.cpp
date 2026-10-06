// Board.fen.
#include "en_passant.hpp"
#include "fen.hpp"
#include "notation.hpp"

namespace sbm {

namespace {

void append_placement(std::string& fen, const Position& position) {
    for (int rank = 7; rank >= 0; --rank) {
        int empty = 0;
        for (int file = 0; file < 8; ++file) {
            const int piece = position.piece_at(make_square(file, rank));
            if (piece == kNoPiece) {
                ++empty;
                continue;
            }
            if (empty > 0) {
                fen += static_cast<char>('0' + empty);
                empty = 0;
            }
            fen += kPieceLetters[piece];
        }
        if (empty > 0) {
            fen += static_cast<char>('0' + empty);
        }
        if (rank > 0) {
            fen += '/';
        }
    }
}

void append_castling(std::string& fen, int castling) {
    if (castling == 0) {
        fen += '-';
        return;
    }
    constexpr std::string_view kLetters = "KQkq";
    for (int index = 0; index < 4; ++index) {
        if ((castling & (1 << index)) != 0) {
            fen += kLetters[index];
        }
    }
}

} // namespace

std::string write_fen(const Position& position) {
    std::string fen;
    append_placement(fen, position);
    fen += position.side_to_move == kWhite ? " w " : " b ";
    append_castling(fen, position.castling);
    fen += ' ';
    const int en_passant = legal_en_passant_square(position);
    if (en_passant == kNoSquare) {
        fen += '-';
    } else {
        append_square(fen, en_passant);
    }
    fen += ' ';
    fen += std::to_string(position.halfmove_clock);
    fen += ' ';
    fen += std::to_string(position.fullmove_number);
    return fen;
}

} // namespace sbm
