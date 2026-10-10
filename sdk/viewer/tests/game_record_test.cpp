#include "check.hpp"
#include "model/game_record.hpp"

using namespace sbm_viewer;

namespace {

constexpr const char* start_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
constexpr const char* after_e4 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1";

StartMessage white_start() {
    StartMessage start;
    start.bot = "Mine";
    start.color = "white";
    start.opponent = "Random";
    start.start_fen = start_fen;
    start.initial_time_ms = 60000;
    return start;
}

MoveMessage move(int ply, const char* uci, const char* fen, bool by_bot) {
    MoveMessage message;
    message.ply = ply;
    message.move = uci;
    message.fen = fen;
    message.by_bot = by_bot;
    return message;
}

void records_moves_with_san() {
    GameRecord game(white_start());
    CHECK(game.ply_count() == 0);
    CHECK(game.add_move(move(1, "e2e4", after_e4, true)));
    CHECK(game.ply_count() == 1);
    CHECK(game.ply(1).san == "e4");
    CHECK(game.ply(1).by_bot);
    CHECK(game.position(0).fen() == start_fen);
    CHECK(game.position(1).fen() == after_e4);
    CHECK(game.position(7).fen() == after_e4);
}

void ignores_repeated_moves() {
    GameRecord game(white_start());
    CHECK(game.add_move(move(1, "e2e4", after_e4, true)));
    CHECK(!game.add_move(move(1, "d2d4", "x", true)));
    CHECK(game.ply_count() == 1);
}

void adopts_the_given_position() {
    GameRecord game(white_start());
    const char* other = "4k3/8/8/8/8/8/8/4K3 b - - 0 1";
    CHECK(game.add_move(move(1, "e2e4", other, true)));
    CHECK(game.position(1).fen() == other);

    // An illegal move keeps the SAN as UCI and still takes the position.
    CHECK(game.add_move(move(2, "a1a2", start_fen, false)));
    CHECK(game.ply(2).san == "a1a2");
    CHECK(game.position(2).fen() == start_fen);
}

void falls_back_to_the_standard_start() {
    StartMessage start = white_start();
    start.start_fen = "garbage";
    const GameRecord game(start);
    CHECK(game.position(0).fen() == start_fen);
}

void carries_clocks_over() {
    GameRecord game(white_start());
    MoveMessage first = move(1, "e2e4", after_e4, true);
    first.white_ms = 59000;
    first.black_ms = 60000;
    game.add_move(first);
    game.add_move(
        move(2, "e7e5", "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2", false));
    CHECK(game.clocks(0).white_ms == 60000);
    CHECK(game.clocks(1).white_ms == 59000);
    CHECK(game.clocks(2).white_ms == 59000);
    CHECK(game.clocks(2).black_ms == 60000);

    StartMessage untimed = white_start();
    untimed.initial_time_ms = 0;
    CHECK(!GameRecord(untimed).clocks(0).white_ms);
}

void keeps_logs_and_the_result() {
    GameRecord game(white_start());
    game.add_log(LogMessage{LogLevel::info, "before", ""});
    game.add_move(move(1, "e2e4", after_e4, true));
    game.add_log(LogMessage{LogLevel::info, "after", ""});
    CHECK(game.logs().size() == 2);
    CHECK(game.logs()[0].ply == 0);
    CHECK(game.logs()[1].ply == 1);

    game.finish(GameOverMessage{"1-0", "resignation"});
    game.finish(GameOverMessage{"0-1", "timeout"});
    CHECK(game.result()->result == "1-0");
    CHECK(!game.add_move(move(2, "e7e5", "x", false)));
}

} // namespace

void test_game_record() {
    records_moves_with_san();
    ignores_repeated_moves();
    adopts_the_given_position();
    falls_back_to_the_standard_start();
    carries_clocks_over();
    keeps_logs_and_the_result();
}
