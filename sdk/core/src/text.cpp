#include "text.hpp"

#include "fen.hpp"
#include "notation.hpp"

namespace sbm {

std::string write_text(const Position& position) {
    std::string text;
    for (int rank = 7; rank >= 0; --rank) {
        for (int file = 0; file < 8; ++file) {
            const int piece = position.piece_at(make_square(file, rank));
            text += piece == kNoPiece ? '.' : kPieceLetters[piece];
            text += file < 7 ? ' ' : '\n';
        }
    }
    text += write_fen(position);
    text += '\n';
    return text;
}

} // namespace sbm
