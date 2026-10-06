#include "position.hpp"

namespace sbm {

namespace {

constexpr std::array<PieceType, 8> kBackRank{kRook, kKnight, kBishop, kQueen,
                                             kKing, kBishop, kKnight, kRook};

} // namespace

Position::Position() {
    squares.fill(kNoPiece);
}

void Position::put(int piece, int square) {
    pieces[piece] |= square_bb(square);
    colors[color_of(piece)] |= square_bb(square);
    squares[square] = static_cast<std::uint8_t>(piece);
}

void Position::remove(int square) {
    const int piece = squares[square];
    pieces[piece] &= ~square_bb(square);
    colors[color_of(piece)] &= ~square_bb(square);
    squares[square] = kNoPiece;
}

Position start_position() {
    Position position;
    for (int file = 0; file < 8; ++file) {
        position.put(make_piece(kWhite, kBackRank[file]), make_square(file, 0));
        position.put(make_piece(kWhite, kPawn), make_square(file, 1));
        position.put(make_piece(kBlack, kPawn), make_square(file, 6));
        position.put(make_piece(kBlack, kBackRank[file]), make_square(file, 7));
    }
    position.castling = kWhiteKingside | kWhiteQueenside | kBlackKingside | kBlackQueenside;
    return position;
}

} // namespace sbm
