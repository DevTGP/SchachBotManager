// All games of one viewer window, fed line by line from the SDK.
#pragma once

#include <string_view>
#include <vector>

#include "game_record.hpp"

namespace sbm_viewer {

class Session {
public:
    // Reads one line and applies it. An unreadable line becomes a warning in the log, a move
    // before the first start is dropped, and log lines before it wait for the first game.
    void apply_line(std::string_view line);
    void apply(Message message);

    const std::vector<GameRecord>& games() const {
        return games_;
    }

private:
    void add_log(LogMessage log);

    std::vector<GameRecord> games_;
    std::vector<LogMessage> early_logs_;
};

} // namespace sbm_viewer
