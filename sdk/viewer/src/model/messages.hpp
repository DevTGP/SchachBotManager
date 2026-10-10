// Lines from the SDK (spec/protocol/viewer-v1/), read into plain structs.
#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <variant>
#include <vector>

namespace sbm_viewer {

struct StartMessage {
    std::string bot;
    std::string color; // "white" or "black"
    std::string opponent;
    std::string start_fen;
    int64_t initial_time_ms = 0;
    int64_t increment_ms = 0;
    std::string discipline; // empty if the game has none
};

struct SearchInfo {
    std::optional<int> depth;
    std::optional<int> seldepth;
    std::optional<int> score_cp;
    std::optional<int> score_mate;
    std::optional<int64_t> nodes;
    std::vector<std::string> pv;
    std::string text;
};

struct MoveMessage {
    int ply = 0;
    std::string move;
    std::string fen;
    bool by_bot = false;
    std::optional<int64_t> white_ms;
    std::optional<int64_t> black_ms;
    std::optional<int64_t> elapsed_ms;
    std::optional<SearchInfo> info;
};

enum class LogLevel { debug, info, warn, error };

struct LogMessage {
    LogLevel level = LogLevel::info;
    std::string text;
    std::string time;
};

struct GameOverMessage {
    std::string result;
    std::string termination;
};

using Message = std::variant<StartMessage, MoveMessage, LogMessage, GameOverMessage>;

// Either a message or the reason the line was not understood. Unknown fields are ignored, so an
// older viewer reads lines of a newer SDK.
struct ParsedLine {
    std::optional<Message> message;
    std::string error;
};

ParsedLine parse_line(std::string_view line);

} // namespace sbm_viewer
