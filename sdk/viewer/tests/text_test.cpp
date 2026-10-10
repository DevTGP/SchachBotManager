#include "check.hpp"
#include "model/notation.hpp"
#include "model/time_text.hpp"

using namespace sbm_viewer;

namespace {

void formats_times() {
    CHECK(clock_text(300000) == "5:00");
    CHECK(clock_text(65000) == "1:05");
    CHECK(clock_text(3900000) == "1:05:00");
    CHECK(clock_text(9350) == "0:09.3");
    CHECK(clock_text(-5) == "0:00.0");
    CHECK(duration_text(850) == "850 ms");
    CHECK(duration_text(12450) == "12.4 s");
    CHECK(duration_text(125000) == "2:05");
}

void builds_move_rows() {
    const auto rows = move_rows(3, 1, false);
    CHECK(rows.size() == 2);
    CHECK(rows[0].number == 1 && rows[0].white_ply == 1 && rows[0].black_ply == 2);
    CHECK(rows[1].number == 2 && rows[1].white_ply == 3 && rows[1].black_ply == 0);

    const auto black = move_rows(2, 7, true);
    CHECK(black.size() == 2);
    CHECK(black[0].number == 7 && black[0].white_ply == 0 && black[0].black_ply == 1);
    CHECK(black[1].number == 8 && black[1].white_ply == 2);

    CHECK(move_rows(0, 1, true).empty());
}

void formats_search_info() {
    SearchInfo info;
    CHECK(score_text(info).empty());
    info.score_cp = 25;
    CHECK(score_text(info) == "+0.25");
    info.score_cp = -150;
    CHECK(score_text(info) == "-1.50");
    info.score_cp = -5;
    CHECK(score_text(info) == "-0.05");
    info.score_cp.reset();
    info.score_mate = -2;
    CHECK(score_text(info) == "#-2");

    CHECK(nodes_text(950) == "950");
    CHECK(nodes_text(12345) == "12.3k");
    CHECK(nodes_text(4500000) == "4.5M");
    CHECK(nodes_text(45000000) == "45.0M");

    const auto start =
        Position::from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
    CHECK(start.has_value());
    if (start) {
        CHECK(pv_text(*start, {"e2e4", "e7e5", "g1f3"}) == "e4 e5 Nf3");
        CHECK(pv_text(*start, {"e2e4", "e2e4", "g1f3"}) == "e4");
    }
}

} // namespace

void test_texts() {
    formats_times();
    builds_move_rows();
    formats_search_info();
}
