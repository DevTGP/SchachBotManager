// One game as the viewer saw it: positions after every half-move, clocks, search info and logs.
#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

#include "messages.hpp"
#include "position.hpp"

namespace sbm_viewer {

struct PlyRecord {
    std::string uci;
    std::string san;
    bool by_bot = false;
    std::optional<int64_t> white_ms;
    std::optional<int64_t> black_ms;
    std::optional<int64_t> elapsed_ms;
    std::optional<SearchInfo> info;
};

struct LogLine {
    LogMessage message;
    // Half-moves played when the line arrived; lines up to the shown half-move are current.
    int ply = 0;
};

struct Clocks {
    std::optional<int64_t> white_ms;
    std::optional<int64_t> black_ms;
};

class GameRecord {
public:
    // An unreadable start FEN falls back to the standard start position.
    explicit GameRecord(StartMessage start);

    const StartMessage& start() const {
        return start_;
    }
    int ply_count() const {
        return static_cast<int>(plies_.size());
    }
    // Position after `ply` half-moves (0 is the start), clamped to the moves known.
    const Position& position(int ply) const;
    // The half-move number `ply`, counted from 1.
    const PlyRecord& ply(int ply) const;
    // Remaining times after `ply` half-moves; missing values carry over from earlier ones.
    Clocks clocks(int ply) const;
    bool bot_is_white() const {
        return start_.color == "white";
    }

    // Appends the next half-move. A repeated or older half-move is ignored (false). If the move
    // does not lead to the given FEN, the viewer adopts the FEN.
    bool add_move(const MoveMessage& move);
    void add_log(LogMessage log);
    void finish(GameOverMessage result);

    const std::vector<LogLine>& logs() const {
        return logs_;
    }
    const std::optional<GameOverMessage>& result() const {
        return result_;
    }

private:
    StartMessage start_;
    std::vector<Position> positions_;
    std::vector<PlyRecord> plies_;
    std::vector<LogLine> logs_;
    std::optional<GameOverMessage> result_;
};

} // namespace sbm_viewer
