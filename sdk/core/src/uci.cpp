#include "uci.hpp"

#include "notation.hpp"

namespace sbm {

namespace {

// Promotion letters in the order of the promotion flags.
constexpr std::string_view kPromotionLetters = "nbrq";

} // namespace

std::optional<Move> parse_uci(std::string_view text) {
    if (text.size() != 4 && text.size() != 5) {
        return std::nullopt;
    }
    const int from = parse_square(text.substr(0, 2));
    const int to = parse_square(text.substr(2, 2));
    if (from == kNoSquare || to == kNoSquare) {
        return std::nullopt;
    }
    if (text.size() == 4) {
        return encode_move(from, to, kQuiet);
    }
    const auto promotion = kPromotionLetters.find(text[4]);
    if (promotion == std::string_view::npos) {
        return std::nullopt;
    }
    return encode_move(from, to, kPromotion + static_cast<int>(promotion));
}

std::optional<std::string> write_uci(Move move) {
    if (move == kNullMove || move == kResign || !has_valid_flags(move)) {
        return std::nullopt;
    }
    std::string text;
    append_square(text, from_square(move));
    append_square(text, to_square(move));
    if (is_promotion(move)) {
        text += kPromotionLetters[move_flags(move) & 3];
    }
    return text;
}

} // namespace sbm
