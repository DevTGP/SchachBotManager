"""The sbm-arena command."""

import pytest
from arena_bots import FIRST_MOVE, write_bot

from sbm.arena.cli import main


def test_series_with_pgn(tmp_path, capsys):
    bot = write_bot(tmp_path, "first", FIRST_MOVE)
    pgn = tmp_path / "games.pgn"
    pgn.write_text("", encoding="utf-8")
    argv = [str(bot), str(bot), "--games", "2", "--max-moves", "2", "--pgn", str(pgn), "--moves"]
    assert main([*argv, "--quiet"]) == 0
    out = capsys.readouterr().out
    assert "Game 1/2: first-1 (White) vs first-2 (Black)" in out
    assert "Game 2/2: first-2 (White) vs first-1 (Black)" in out
    assert "1. " in out and "1... " in out
    assert out.count("1/2-1/2 max_moves") == 2
    games = pgn.read_text(encoding="utf-8").split("[Event ")
    assert len(games) == 3
    assert '[Round "2"]' in games[2] and '[White "first-2"]' in games[2]


def test_replay(tmp_path, capsys):
    bot = write_bot(tmp_path, "first", FIRST_MOVE)
    pgn = tmp_path / "game.pgn"
    pgn.write_text("1. e4 e5 2. Nf3 Nc6 *", encoding="utf-8")
    argv = [str(bot), str(bot), "--replay", str(pgn), "--replay-ply", "3", "--max-moves", "1"]
    assert main([*argv, "--moves", "--quiet"]) == 0
    captured = capsys.readouterr()
    fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2"
    assert f"start position from {pgn}: {fen}" in captured.err
    assert "2... " in captured.out


@pytest.mark.parametrize(
    "argv",
    [
        ["a.py"],
        ["missing.py", "tcp"],
        ["tcp", "tcp"],
        ["tcp", "tcp:1", "--time", "0"],
        ["tcp", "tcp:1", "--games", "0"],
        ["tcp", "tcp:1", "--fen", "not a fen"],
        ["tcp", "tcp:1", "--replay-ply", "3"],
        ["tcp", "tcp:1", "--replay", "missing.pgn"],
        ["tcp", "tcp:1", "--replay", "missing.pgn", "--fen", "8/8/8/8/8/8/8/8 w - - 0 1"],
        ["tcp", "tcp:1", "--replay-ply", "-1"],
    ],
)
def test_usage_errors(argv, capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(argv)
    assert exit_info.value.code == 2
    assert "usage: sbm-arena" in capsys.readouterr().err
