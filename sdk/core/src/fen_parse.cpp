// Board.from_fen: syntax first, then the position rules of spec/api/board.json.
#include <array>
#include <cstdint>
#include <limits>

#include "fen.hpp"
#include "notation.hpp"
#include "threats.hpp"

namespace sbm {

namespace {

constexpr int kMaxPiecesPerColor = 16;
constexpr std::string_view kCastlingLetters = "KQkq";
constexpr std::array<int, 4> kCastlingBits{
    kWhiteKingside, kWhiteQueenside, kBlackKingside, kBlackQueenside};

// Exactly N parts separated by single separators; empty parts are kept.
template <std::size_t N>
std::optional<std::array<std::string_view, N>> split_exact(std::string_view text, char separator) {
    std::array<std::string_view, N> parts;
    std::size_t count = 0;
    std::size_t start = 0;
    for (std::size_t i = 0; i <= text.size(); ++i) {
        if (i == text.size() || text[i] == separator) {
            if (count == N) {
                return std::nullopt;
            }
            parts[count++] = text.substr(start, i - start);
            start = i + 1;
        }
    }
    if (count != N) {
        return std::nullopt;
    }
    return parts;
}

bool is_digit(char c) {
    return c >= '0' && c <= '9';
}

// One rank of the placement, from file a to h: piece letters and digits 1 to 8, no two digits
// in a row, eight squares in total.
bool parse_rank(std::string_view text, int rank, Position& position) {
    int file = 0;
    bool after_digit = false;
    if (text.empty()) {
        return false;
    }
    for (const char c : text) {
        if (c >= '1' && c <= '8') {
            if (after_digit) {
                return false;
            }
            file += c - '0';
            after_digit = true;
            continue;
        }
        const int piece = piece_from_letter(c);
        if (piece == kNoPiece || file >= 8) {
            return false;
        }
        position.put(piece, make_square(file, rank));
        ++file;
        after_digit = false;
    }
    return file == 8;
}

bool parse_placement(std::string_view text, Position& position) {
    const auto ranks = split_exact<8>(text, '/');
    if (!ranks) {
        return false;
    }
    for (int index = 0; index < 8; ++index) {
        if (!parse_rank((*ranks)[index], 7 - index, position)) {
            return false;
        }
    }
    return true;
}

// "-" or a non-empty selection of KQkq in this order.
std::optional<int> parse_castling(std::string_view text) {
    if (text == "-") {
        return 0;
    }
    int rights = 0;
    std::size_t next = 0;
    for (const char c : text) {
        const auto index = kCastlingLetters.find(c, next);
        if (index == std::string_view::npos) {
            return std::nullopt;
        }
        rights |= kCastlingBits[index];
        next = index + 1;
    }
    return text.empty() ? std::nullopt : std::optional<int>(rights);
}

std::optional<int> parse_en_passant(std::string_view text) {
    if (text == "-") {
        return kNoSquare;
    }
    const int square = parse_square(text);
    if (square == kNoSquare || (rank_of(square) != 2 && rank_of(square) != 5)) {
        return std::nullopt;
    }
    return square;
}

// Decimal without leading zeros, at most the largest 32-bit integer.
std::optional<int> parse_counter(std::string_view text, int minimum) {
    constexpr std::int64_t kMax = std::numeric_limits<std::int32_t>::max();
    if (text.empty() || text.size() > 10 || (text.size() > 1 && text[0] == '0')) {
        return std::nullopt;
    }
    std::int64_t value = 0;
    for (const char c : text) {
        if (!is_digit(c)) {
            return std::nullopt;
        }
        value = value * 10 + (c - '0');
    }
    if (value < minimum || value > kMax) {
        return std::nullopt;
    }
    return static_cast<int>(value);
}

bool has_castling_pieces(const Position& position) {
    for (int index = 0; index < 4; ++index) {
        if ((position.castling & kCastlingBits[index]) == 0) {
            continue;
        }
        const Color color = index < 2 ? kWhite : kBlack;
        const int rank = color == kWhite ? 0 : 7;
        const int rook_file = index % 2 == 0 ? 7 : 0;
        if (position.piece_at(make_square(4, rank)) != make_piece(color, kKing) ||
            position.piece_at(make_square(rook_file, rank)) != make_piece(color, kRook)) {
            return false;
        }
    }
    return true;
}

// The square a pawn of the side not to move just passed with a double push.
bool has_valid_en_passant(const Position& position) {
    const int square = position.en_passant;
    if (square == kNoSquare) {
        return true;
    }
    const Color us = position.side_to_move;
    const int forward = us == kWhite ? 8 : -8;
    return rank_of(square) == (us == kWhite ? 5 : 2) && position.piece_at(square) == kNoPiece &&
           position.piece_at(square + forward) == kNoPiece &&
           position.piece_at(square - forward) == make_piece(opposite(us), kPawn);
}

bool is_valid_position(const Position& position) {
    for (const Color color : {kWhite, kBlack}) {
        if (popcount(position.pieces_of(color, kKing)) != 1 ||
            popcount(position.colors[color]) > kMaxPiecesPerColor) {
            return false;
        }
    }
    const Bitboard pawns = position.pieces_of(kWhite, kPawn) | position.pieces_of(kBlack, kPawn);
    if ((pawns & (rank_bb(0) | rank_bb(7))) != 0) {
        return false;
    }
    const Color us = position.side_to_move;
    if (is_attacked(position, position.king_square(opposite(us)), us)) {
        return false;
    }
    return has_castling_pieces(position) && has_valid_en_passant(position);
}

} // namespace

std::optional<Position> parse_fen(std::string_view fen) {
    const auto fields = split_exact<6>(fen, ' ');
    if (!fields) {
        return std::nullopt;
    }
    const auto& [placement, side, castling, en_passant, halfmove, fullmove] = *fields;
    Position position;
    if (!parse_placement(placement, position) || (side != "w" && side != "b")) {
        return std::nullopt;
    }
    const auto rights = parse_castling(castling);
    const auto square = parse_en_passant(en_passant);
    const auto halfmove_clock = parse_counter(halfmove, 0);
    const auto fullmove_number = parse_counter(fullmove, 1);
    if (!rights || !square || !halfmove_clock || !fullmove_number) {
        return std::nullopt;
    }
    position.side_to_move = side == "w" ? kWhite : kBlack;
    position.castling = *rights;
    position.en_passant = *square;
    position.halfmove_clock = *halfmove_clock;
    position.fullmove_number = *fullmove_number;
    if (!is_valid_position(position)) {
        return std::nullopt;
    }
    return position;
}

} // namespace sbm
