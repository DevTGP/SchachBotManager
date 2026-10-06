"""The arena's console output."""

import io

from sbm.arena.report import ConsoleReport
from sbm.arena.series import Game, Score
from sbm.referee import STANDARD_FEN, MatchRecord, MoveRecord, Outcome, SideRecord


def move(ply: int, san: str, info: dict | None = None) -> MoveRecord:
    return MoveRecord(ply, "a1a1", san, STANDARD_FEN, 1234, 1000, info)


def test_move_labels():
    report = ConsoleReport(io.StringIO(), STANDARD_FEN, 1)
    assert report.move_label(move(1, "e4")) == "1. e4"
    assert report.move_label(move(2, "e5")) == "1... e5"
    assert report.move_label(move(3, "Nf3")) == "2. Nf3"
    black_first = ConsoleReport(io.StringIO(), "4k3/8/8/8/8/8/8/4K3 b - - 0 12", 1)
    assert black_first.move_label(move(1, "Kd8")) == "12... Kd8"
    assert black_first.move_label(move(2, "Kd1")) == "13. Kd1"


def test_game_lines():
    out = io.StringIO()
    report = ConsoleReport(out, STANDARD_FEN, 2)
    game = Game(1, "alpha", "beta")
    report.start(game)
    report.move(move(1, "e4", {"depth": 3, "score_cp": 25, "text": "a\nb"}))
    outcome = Outcome("1-0", "resignation", 0, "Black resigned")
    report.end(
        game, MatchRecord(STANDARD_FEN, SideRecord("alpha"), SideRecord("beta"), [], outcome)
    )
    lines = out.getvalue().splitlines()
    assert lines[0] == "Game 1/2: alpha (White) vs beta (Black)"
    assert lines[1].split() == [
        "1.",
        "e4",
        "1.234",
        "s",
        "depth",
        "3,",
        "score",
        "+0.25,",
        "a",
        "b",
    ]
    assert lines[2] == "  1-0 resignation: Black resigned"


def test_scores_sorted_by_points():
    out = io.StringIO()
    ConsoleReport(out, STANDARD_FEN, 3).scores(
        {"weak": Score(losses=2, draws=1), "a-strong-bot": Score(wins=2, draws=1)}
    )
    lines = out.getvalue().splitlines()
    assert lines[1].split() == ["Bot", "Points", "Won", "Drawn", "Lost", "Unfinished"]
    assert lines[2].split() == ["a-strong-bot", "2.5", "2", "1", "0", "0"]
    assert lines[3].split() == ["weak", "0.5", "0", "1", "2", "0"]
