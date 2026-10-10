#include "messages.hpp"

#include <nlohmann/json.hpp>

namespace sbm_viewer {

namespace {

using nlohmann::json;

std::optional<std::string> text_field(const json& object, const char* key) {
    const auto found = object.find(key);
    if (found == object.end() || !found->is_string()) {
        return std::nullopt;
    }
    return found->get<std::string>();
}

std::optional<int64_t> integer_field(const json& object, const char* key) {
    const auto found = object.find(key);
    if (found == object.end() || !found->is_number_integer()) {
        return std::nullopt;
    }
    return found->get<int64_t>();
}

std::optional<int> small_field(const json& object, const char* key) {
    const auto value = integer_field(object, key);
    if (!value || *value < -1'000'000 || *value > 1'000'000) {
        return std::nullopt;
    }
    return static_cast<int>(*value);
}

ParsedLine failure(std::string reason) {
    return ParsedLine{std::nullopt, std::move(reason)};
}

ParsedLine parse_start(const json& object) {
    StartMessage start;
    const auto bot = text_field(object, "bot");
    const auto color = text_field(object, "color");
    const auto opponent = text_field(object, "opponent");
    const auto fen = text_field(object, "start_fen");
    if (!bot || !opponent || !fen || !color || (*color != "white" && *color != "black")) {
        return failure("start without bot, color, opponent or start_fen");
    }
    start.bot = *bot;
    start.color = *color;
    start.opponent = *opponent;
    start.start_fen = *fen;
    start.initial_time_ms = integer_field(object, "initial_time_ms").value_or(0);
    start.increment_ms = integer_field(object, "increment_ms").value_or(0);
    start.discipline = text_field(object, "discipline").value_or("");
    return ParsedLine{Message{std::move(start)}, {}};
}

SearchInfo parse_info(const json& object) {
    SearchInfo info;
    info.depth = small_field(object, "depth");
    info.seldepth = small_field(object, "seldepth");
    info.score_cp = small_field(object, "score_cp");
    info.score_mate = small_field(object, "score_mate");
    info.nodes = integer_field(object, "nodes");
    const auto pv = object.find("pv");
    if (pv != object.end() && pv->is_array()) {
        for (const auto& move : *pv) {
            if (!move.is_string()) {
                break;
            }
            info.pv.push_back(move.get<std::string>());
        }
    }
    info.text = text_field(object, "text").value_or("");
    return info;
}

ParsedLine parse_move(const json& object) {
    MoveMessage move;
    const auto ply = small_field(object, "ply");
    const auto uci = text_field(object, "move");
    const auto fen = text_field(object, "fen");
    const auto by = text_field(object, "by");
    if (!ply || *ply < 1 || !uci || !fen || !by || (*by != "bot" && *by != "opponent")) {
        return failure("move without ply, move, fen or by");
    }
    move.ply = *ply;
    move.move = *uci;
    move.fen = *fen;
    move.by_bot = *by == "bot";
    move.white_ms = integer_field(object, "white_ms");
    move.black_ms = integer_field(object, "black_ms");
    move.elapsed_ms = integer_field(object, "elapsed_ms");
    const auto info = object.find("info");
    if (info != object.end() && info->is_object()) {
        move.info = parse_info(*info);
    }
    return ParsedLine{Message{std::move(move)}, {}};
}

ParsedLine parse_log(const json& object) {
    LogMessage log;
    const auto level = text_field(object, "level").value_or("info");
    if (level == "debug") {
        log.level = LogLevel::debug;
    } else if (level == "warn") {
        log.level = LogLevel::warn;
    } else if (level == "error") {
        log.level = LogLevel::error;
    }
    log.text = text_field(object, "text").value_or("");
    log.time = text_field(object, "time").value_or("");
    return ParsedLine{Message{std::move(log)}, {}};
}

ParsedLine parse_game_over(const json& object) {
    GameOverMessage over;
    const auto result = text_field(object, "result");
    if (!result) {
        return failure("game_over without result");
    }
    over.result = *result;
    over.termination = text_field(object, "termination").value_or("");
    return ParsedLine{Message{std::move(over)}, {}};
}

} // namespace

ParsedLine parse_line(std::string_view line) {
    const json object = json::parse(line, nullptr, false);
    if (object.is_discarded() || !object.is_object()) {
        return failure("not a JSON object");
    }
    const auto type = text_field(object, "type").value_or("");
    if (type == "start") {
        return parse_start(object);
    }
    if (type == "move") {
        return parse_move(object);
    }
    if (type == "log") {
        return parse_log(object);
    }
    if (type == "game_over") {
        return parse_game_over(object);
    }
    return failure("unknown type '" + type + "'");
}

} // namespace sbm_viewer
