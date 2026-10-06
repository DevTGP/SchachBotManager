// Letters of pieces and names of squares as used by FEN, UCI and SAN.
#pragma once

#include <string>
#include <string_view>

#include "bitboard.hpp"
#include "piece.hpp"

namespace sbm {

// FEN letter of each piece code: upper case for white, lower case for black.
inline constexpr std::string_view kPieceLetters = "PNBRQKpnbrqk";

// The piece of a FEN letter, or kNoPiece.
constexpr int piece_from_letter(char letter) {
    const auto index = kPieceLetters.find(letter);
    return index == std::string_view::npos ? kNoPiece : static_cast<int>(index);
}

constexpr char file_letter(int square) {
    return static_cast<char>('a' + file_of(square));
}

constexpr char rank_digit(int square) {
    return static_cast<char>('1' + rank_of(square));
}

// The square named by two characters such as "e4", or kNoSquare.
constexpr int parse_square(std::string_view text) {
    if (text.size() != 2 || text[0] < 'a' || text[0] > 'h' || text[1] < '1' || text[1] > '8') {
        return kNoSquare;
    }
    return make_square(text[0] - 'a', text[1] - '1');
}

inline void append_square(std::string& text, int square) {
    text += file_letter(square);
    text += rank_digit(square);
}

} // namespace sbm
