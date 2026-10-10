#include "session.hpp"

#include <type_traits>
#include <utility>

namespace sbm_viewer {

void Session::apply_line(std::string_view line) {
    if (line.find_first_not_of(" \t\r") == std::string_view::npos) {
        return;
    }
    ParsedLine parsed = parse_line(line);
    if (parsed.message) {
        apply(std::move(*parsed.message));
        return;
    }
    add_log(LogMessage{LogLevel::warn, "viewer: unreadable line (" + parsed.error + ")", ""});
}

void Session::apply(Message message) {
    std::visit(
        [this](auto&& value) {
            using T = std::decay_t<decltype(value)>;
            if constexpr (std::is_same_v<T, StartMessage>) {
                games_.emplace_back(std::move(value));
                for (LogMessage& log : early_logs_) {
                    games_.back().add_log(std::move(log));
                }
                early_logs_.clear();
            } else if constexpr (std::is_same_v<T, LogMessage>) {
                add_log(std::move(value));
            } else if (!games_.empty()) {
                if constexpr (std::is_same_v<T, MoveMessage>) {
                    games_.back().add_move(value);
                } else {
                    games_.back().finish(std::move(value));
                }
            }
        },
        message);
}

void Session::add_log(LogMessage log) {
    if (games_.empty()) {
        early_logs_.push_back(std::move(log));
    } else {
        games_.back().add_log(std::move(log));
    }
}

} // namespace sbm_viewer
