#include "game_record.hpp"

#include <algorithm>
#include <utility>

namespace sbm_viewer {

namespace {

constexpr const char* standard_start = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

Position start_position(const std::string& fen) {
    if (auto position = Position::from_fen(fen)) {
        return std::move(*position);
    }
    return *Position::from_fen(standard_start);
}

} // namespace

GameRecord::GameRecord(StartMessage start) : start_(std::move(start)) {
    positions_.push_back(start_position(start_.start_fen));
}

const Position& GameRecord::position(int ply) const {
    const int index = std::clamp(ply, 0, ply_count());
    return positions_[static_cast<size_t>(index)];
}

const PlyRecord& GameRecord::ply(int ply) const {
    const int index = std::clamp(ply, 1, ply_count()) - 1;
    return plies_[static_cast<size_t>(index)];
}

Clocks GameRecord::clocks(int ply) const {
    Clocks clocks;
    if (start_.initial_time_ms > 0) {
        clocks.white_ms = start_.initial_time_ms;
        clocks.black_ms = start_.initial_time_ms;
    }
    const int last = std::clamp(ply, 0, ply_count());
    for (int index = 0; index < last; ++index) {
        const PlyRecord& record = plies_[static_cast<size_t>(index)];
        if (record.white_ms) {
            clocks.white_ms = record.white_ms;
        }
        if (record.black_ms) {
            clocks.black_ms = record.black_ms;
        }
    }
    return clocks;
}

bool GameRecord::add_move(const MoveMessage& move) {
    if (result_ || move.ply <= ply_count()) {
        return false;
    }
    Position next = positions_.back();
    PlyRecord record;
    record.uci = move.move;
    record.san = next.san(move.move).value_or(move.move);
    record.by_bot = move.by_bot;
    record.white_ms = move.white_ms;
    record.black_ms = move.black_ms;
    record.elapsed_ms = move.elapsed_ms;
    record.info = move.info;
    const bool played = next.play(move.move);
    if (!played || next.fen() != move.fen) {
        if (auto given = Position::from_fen(move.fen)) {
            next = std::move(*given);
        }
    }
    positions_.push_back(std::move(next));
    plies_.push_back(std::move(record));
    return true;
}

void GameRecord::add_log(LogMessage log) {
    logs_.push_back(LogLine{std::move(log), ply_count()});
}

void GameRecord::finish(GameOverMessage result) {
    if (!result_) {
        result_ = std::move(result);
    }
}

} // namespace sbm_viewer
