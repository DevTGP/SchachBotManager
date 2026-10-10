// A chess position on the core's board (C interface); the viewer has no rules of its own.
#pragma once

#include <memory>
#include <optional>
#include <string>

#include "sbm/sbm.h"

namespace sbm_viewer {

class Position {
public:
    // nullopt if the core rejects the FEN.
    static std::optional<Position> from_fen(const std::string& fen);

    Position(const Position& other);
    Position& operator=(const Position& other);
    Position(Position&&) noexcept = default;
    Position& operator=(Position&&) noexcept = default;
    ~Position() = default;

    // Piece as in the core (color * 6 + type), SBM_NO_PIECE for an empty square.
    int piece_at(int square) const;
    int side_to_move() const;
    int fullmove_number() const;
    // Square of the king of the side to move if it is in check, otherwise SBM_NO_SQUARE.
    int checked_king() const;
    std::string fen() const;

    // SAN of a legal move given in UCI without playing it; nullopt if it is not legal.
    std::optional<std::string> san(const std::string& uci) const;
    // Plays a legal move given in UCI; false leaves the position unchanged.
    bool play(const std::string& uci);

private:
    struct Free {
        void operator()(sbm_board* board) const {
            sbm_board_free(board);
        }
    };
    explicit Position(sbm_board* board);
    std::optional<sbm_move> parse(const std::string& uci) const;

    std::unique_ptr<sbm_board, Free> board_;
};

} // namespace sbm_viewer
