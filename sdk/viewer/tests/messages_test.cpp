#include <variant>

#include "check.hpp"
#include "model/messages.hpp"

using namespace sbm_viewer;

namespace {

void reads_start() {
    const auto parsed = parse_line(
        R"({"type":"start","v":1,"bot":"Mine","color":"black","opponent":"Random",)"
        R"("start_fen":"8/8/8/8/8/8/8/K6k w - - 0 1","initial_time_ms":60000,"increment_ms":500,)"
        R"("discipline":"Blitz"})");
    CHECK(parsed.message.has_value());
    const auto* start = std::get_if<StartMessage>(&*parsed.message);
    CHECK(start != nullptr);
    if (start != nullptr) {
        CHECK(start->bot == "Mine");
        CHECK(start->color == "black");
        CHECK(start->opponent == "Random");
        CHECK(start->initial_time_ms == 60000);
        CHECK(start->increment_ms == 500);
        CHECK(start->discipline == "Blitz");
    }
}

void reads_move_with_info() {
    const auto parsed = parse_line(
        R"({"type":"move","ply":1,"move":"e2e4","fen":"x","by":"bot","white_ms":299500,)"
        R"("elapsed_ms":500,"info":{"depth":3,"score_mate":-2,"nodes":1234,"pv":["e2e4","e7e5"],)"
        R"("text":"hi","future":true},"future":1})");
    const auto* move = std::get_if<MoveMessage>(&*parsed.message);
    CHECK(move != nullptr);
    if (move != nullptr) {
        CHECK(move->ply == 1);
        CHECK(move->by_bot);
        CHECK(move->white_ms == 299500);
        CHECK(!move->black_ms);
        CHECK(move->elapsed_ms == 500);
        CHECK(move->info.has_value());
        CHECK(move->info->depth == 3);
        CHECK(move->info->score_mate == -2);
        CHECK(!move->info->score_cp);
        CHECK(move->info->nodes == 1234);
        CHECK(move->info->pv.size() == 2);
        CHECK(move->info->text == "hi");
    }
}

void reads_log_and_game_over() {
    const auto log =
        parse_line(R"({"type":"log","level":"warn","text":"slow","time":"12:00:01.250"})");
    const auto* line = std::get_if<LogMessage>(&*log.message);
    CHECK(line != nullptr && line->level == LogLevel::warn && line->text == "slow");

    const auto over = parse_line(
        R"({"type":"game_over","result":"1-0","termination":"checkmate","last_move":"h5f7"})");
    const auto* result = std::get_if<GameOverMessage>(&*over.message);
    CHECK(result != nullptr && result->result == "1-0" && result->termination == "checkmate");
}

void rejects_broken_lines() {
    CHECK(!parse_line("not json").message);
    CHECK(!parse_line("[1,2]").message);
    CHECK(!parse_line(R"({"type":"dance"})").message);
    CHECK(!parse_line(R"({"type":"move","ply":0,"move":"e2e4","fen":"x","by":"bot"})").message);
    CHECK(!parse_line(R"({"type":"move","ply":1,"move":"e2e4","fen":"x","by":"both"})").message);
    CHECK(!parse_line(R"({"type":"start","bot":"A","color":"red","opponent":"B","start_fen":"x"})")
               .message);
    CHECK(!parse_line(R"({"type":"game_over"})").error.empty());
}

} // namespace

void test_messages() {
    reads_start();
    reads_move_with_info();
    reads_log_and_game_over();
    rejects_broken_lines();
}
