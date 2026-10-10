#include "position.hpp"

#include <array>
#include <new>

namespace sbm_viewer {

std::optional<Position> Position::from_fen(const std::string& fen) {
    sbm_board* board = nullptr;
    if (sbm_board_from_fen(fen.c_str(), &board) != SBM_OK) {
        return std::nullopt;
    }
    return Position(board);
}

Position::Position(sbm_board* board) : board_(board) {}

Position::Position(const Position& other) {
    sbm_board* copy = nullptr;
    if (sbm_board_copy(other.board_.get(), &copy) != SBM_OK) {
        throw std::bad_alloc();
    }
    board_.reset(copy);
}

Position& Position::operator=(const Position& other) {
    if (this != &other) {
        Position copy(other);
        board_ = std::move(copy.board_);
    }
    return *this;
}

int Position::piece_at(int square) const {
    sbm_piece piece = SBM_NO_PIECE;
    sbm_board_piece_at(board_.get(), static_cast<sbm_square>(square), &piece);
    return piece;
}

int Position::side_to_move() const {
    sbm_color color = SBM_WHITE;
    sbm_board_side_to_move(board_.get(), &color);
    return color;
}

int Position::fullmove_number() const {
    int32_t number = 1;
    sbm_board_fullmove_number(board_.get(), &number);
    return number;
}

int Position::checked_king() const {
    sbm_bool check = 0;
    sbm_square king = SBM_NO_SQUARE;
    if (sbm_board_is_check(board_.get(), &check) != SBM_OK || check == 0) {
        return SBM_NO_SQUARE;
    }
    sbm_board_king_square(board_.get(), static_cast<sbm_color>(side_to_move()), &king);
    return king;
}

std::string Position::fen() const {
    std::array<char, SBM_FEN_BUFFER_SIZE> buffer{};
    sbm_board_fen(board_.get(), buffer.data(), static_cast<uint32_t>(buffer.size()));
    return buffer.data();
}

std::optional<sbm_move> Position::parse(const std::string& uci) const {
    sbm_move move = SBM_NULL_MOVE;
    if (sbm_board_parse_move(board_.get(), uci.c_str(), &move) != SBM_OK) {
        return std::nullopt;
    }
    return move;
}

std::optional<std::string> Position::san(const std::string& uci) const {
    const auto move = parse(uci);
    std::array<char, SBM_SAN_BUFFER_SIZE> buffer{};
    if (!move ||
        sbm_board_san(board_.get(), *move, buffer.data(), static_cast<uint32_t>(buffer.size())) !=
            SBM_OK) {
        return std::nullopt;
    }
    return std::string(buffer.data());
}

bool Position::play(const std::string& uci) {
    const auto move = parse(uci);
    return move && sbm_board_make_move(board_.get(), *move) == SBM_OK;
}

} // namespace sbm_viewer
