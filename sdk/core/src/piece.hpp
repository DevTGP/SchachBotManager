// Colors, piece types and pieces with the codes of E35: piece = color * 6 + piece type.
#pragma once

namespace sbm {

enum Color : int { kWhite = 0, kBlack = 1 };

enum PieceType : int {
    kPawn = 0,
    kKnight = 1,
    kBishop = 2,
    kRook = 3,
    kQueen = 4,
    kKing = 5,
    kNoPieceType = 6
};

inline constexpr int kColorCount = 2;
inline constexpr int kPieceTypeCount = 6;
inline constexpr int kPieceCount = 12;
inline constexpr int kNoPiece = 12;

constexpr Color opposite(Color color) {
    return static_cast<Color>(color ^ 1);
}

constexpr int make_piece(Color color, PieceType type) {
    return color * kPieceTypeCount + type;
}

constexpr Color color_of(int piece) {
    return static_cast<Color>(piece / kPieceTypeCount);
}

constexpr PieceType type_of(int piece) {
    return static_cast<PieceType>(piece % kPieceTypeCount);
}

} // namespace sbm
