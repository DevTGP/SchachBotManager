#include "run_calls.hpp"

#include <exception>
#include <map>
#include <optional>
#include <set>
#include <string>

#include "board_setup.hpp"
#include "json_values.hpp"

namespace sbm_test {

namespace {

// Move functions that each binding computes from the encoding; the core has no C function.
const std::set<std::string, std::less<>> kWithoutCFunction{
    "Move.create",     "Move.from_value",  "Move.value",         "Move.from_square",
    "Move.to_square",  "Move.flags",       "Move.promotion",     "Move.is_promotion",
    "Move.is_capture", "Move.is_castling", "Move.is_en_passant",
};

// Status code of each error in spec/api/errors.json (E52).
const std::map<std::string, sbm_status, std::less<>> kErrorStatus{
    {"InvalidArgument", SBM_INVALID_ARGUMENT}, {"InvalidFen", SBM_INVALID_FEN},
    {"InvalidUci", SBM_INVALID_UCI},           {"IllegalMove", SBM_ILLEGAL_MOVE},
    {"InvalidState", SBM_INVALID_STATE},
};

std::string status_text(sbm_status status) {
    return std::string(sbm_status_name(status));
}

// The reason the outcome differs from the vector, or nothing if it matches.
std::optional<std::string> check_outcome(const json& vector, sbm_status status, const Call& call) {
    if (vector.contains("error")) {
        const auto error = vector["error"].get<std::string>();
        const auto expected = kErrorStatus.find(error);
        if (expected == kErrorStatus.end()) {
            return "unknown error " + error;
        }
        if (status != expected->second) {
            return "expected " + status_text(expected->second) + ", got " + status_text(status);
        }
    } else if (status != SBM_OK) {
        return "expected ok, got " + status_text(status);
    } else if (vector.contains("result_contains")) {
        const auto part = vector["result_contains"].get<std::string>();
        if (!call.result.is_string() ||
            call.result.get<std::string>().find(part) == std::string::npos) {
            return "result " + call.result.dump() + " does not contain " + part;
        }
    } else if (!same_result(call.result, vector.at("result"), vector.value("unordered", false))) {
        return "expected " + vector["result"].dump() + ", got " + call.result.dump();
    }
    if (vector.contains("board_after")) {
        const auto expected = vector["board_after"].get<std::string>();
        const auto actual = board_fen(call.board);
        if (actual != expected) {
            return "board after: expected " + expected + ", got " + actual;
        }
    }
    return std::nullopt;
}

void run_vector(const json& vector, const Registry& registry, Summary& summary) {
    const auto id = vector.at("id").get<std::string>();
    const auto function = vector.at("function").get<std::string>();
    if (kWithoutCFunction.contains(function)) {
        summary.skip();
        return;
    }
    const auto handler = registry.find(function);
    if (handler == registry.end()) {
        summary.fail(id, "no handler for " + function);
        return;
    }
    try {
        BoardPtr board;
        if (vector.contains("board")) {
            board = setup_board(vector["board"]);
        }
        Call call{vector, board.get(), json()};
        const sbm_status status = handler->second(call);
        if (const auto reason = check_outcome(vector, status, call)) {
            summary.fail(id, *reason);
        } else {
            summary.pass();
        }
    } catch (const std::exception& error) {
        summary.fail(id, error.what());
    }
}

} // namespace

void run_call_vectors(const json& file, const Registry& registry, Summary& summary) {
    for (const auto& vector : file.at("vectors")) {
        run_vector(vector, registry, summary);
    }
}

} // namespace sbm_test
