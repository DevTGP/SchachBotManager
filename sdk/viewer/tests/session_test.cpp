#include "check.hpp"
#include "model/session.hpp"

using namespace sbm_viewer;

namespace {

constexpr const char* start_line =
    R"({"type":"start","v":1,"bot":"Mine","color":"white","opponent":"Random",)"
    R"("start_fen":"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",)"
    R"("initial_time_ms":60000,"increment_ms":0})";
constexpr const char* e4_line =
    R"({"type":"move","ply":1,"move":"e2e4",)"
    R"("fen":"rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1","by":"bot"})";

void collects_games() {
    Session session;
    session.apply_line(e4_line);
    session.apply_line(R"({"type":"log","level":"info","text":"early","time":"00:00:00.000"})");
    session.apply_line("   ");
    CHECK(session.games().empty());

    session.apply_line(start_line);
    session.apply_line(e4_line);
    session.apply_line(R"({"type":"game_over","result":"1-0","termination":"resignation"})");
    session.apply_line(start_line);
    CHECK(session.games().size() == 2);
    const GameRecord& first = session.games()[0];
    CHECK(first.ply_count() == 1);
    CHECK(first.result().has_value());
    CHECK(first.logs().size() == 1);
    CHECK(first.logs()[0].message.text == "early");
    CHECK(session.games()[1].ply_count() == 0);
}

void warns_about_unreadable_lines() {
    Session session;
    session.apply_line(start_line);
    session.apply_line("{broken");
    const auto& logs = session.games()[0].logs();
    CHECK(logs.size() == 1);
    CHECK(logs[0].message.level == LogLevel::warn);
}

} // namespace

void test_session() {
    collects_games();
    warns_about_unreadable_lines();
}
