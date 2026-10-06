"""The Python template project under templates/python."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
from spec_files import SPEC

import sbm
from sbm.arena.cli import _parser
from sbm.bot import take_report

TEMPLATE = Path(__file__).resolve().parents[3] / "templates" / "python"
CLOCK = sbm.Clock(60_000, 60_000, 0)
# Values for the ${input:…} prompts of tasks.json.
INPUTS = {"${input:replayGame}": "1", "${input:replayPly}": "10"}


def load_json(name: str) -> dict:
    return json.loads((TEMPLATE / ".vscode" / name).read_text(encoding="utf-8"))


@pytest.fixture
def template(monkeypatch):
    monkeypatch.setenv("SBM_DATA_DIR", str(TEMPLATE / "data"))
    spec = importlib.util.spec_from_file_location("template_bot", TEMPLATE / "bot.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def bot(template):
    bot = template.TemplateBot()
    fen = sbm.Board().fen()
    bot.on_game_start(sbm.GameInfo("g", sbm.WHITE, "opp", fen, 60_000, 0, 10_000, 256, "test"))
    return bot


def test_book_holds_legal_moves(template):
    book = template.load_book()
    assert len(book) >= 8
    for position, moves in book.items():
        board = sbm.Board.from_fen(f"{position} 0 1")
        assert template.position_key(board) == position
        assert moves
        for uci in moves:
            assert board.is_legal(board.parse_move(uci))


def test_plays_from_the_book(bot):
    board = sbm.Board()
    move = bot.choose_move(board, CLOCK)
    assert move.uci() in {"e2e4", "d2d4", "g1f3", "c2c4"}
    assert take_report(bot).text == "book"


def test_takes_a_hanging_queen_but_not_a_defended_pawn(bot):
    board = sbm.Board.from_fen("4k3/8/8/3q4/8/8/8/3RK3 w - - 0 1")
    assert bot.choose_move(board, CLOCK).uci() == "d1d5"
    assert take_report(bot).score_cp == 900
    board = sbm.Board.from_fen("4k3/8/2p5/3p4/8/8/8/3QK3 w - - 0 1")
    for _ in range(10):
        assert bot.choose_move(board, CLOCK).uci() != "d1d5"


def test_runs_as_script(tmp_path):
    init = (SPEC / "protocol" / "v1" / "examples" / "valid" / "init.standard.json").read_text()
    done = subprocess.run(
        [sys.executable, str(TEMPLATE / "bot.py")],
        input=init.strip() + "\n",
        capture_output=True,
        text=True,
        timeout=30,
        cwd=tmp_path,  # data/ is found next to bot.py, not in the working directory
    )
    assert '"type":"ready"' in done.stdout.replace(" ", ""), done.stderr


def test_tasks_are_valid_arena_calls():
    tasks = load_json("tasks.json")["tasks"]
    for task in tasks:
        assert task["command"] == "${command:python.interpreterPath}"
        assert task["args"][:2] == ["-m", "sbm.arena"]
        args = [INPUTS.get(arg, arg) for arg in task["args"][2:]]
        _parser().parse_args(args)
        if task.get("isBackground"):
            assert "tcp" in args and "--no-clock" in args
            background = task["problemMatcher"]["background"]
            assert background["endsPattern"] == "waiting for .* to connect"


def test_launch_starts_the_bot_after_its_task():
    labels = {task["label"] for task in load_json("tasks.json")["tasks"]}
    configurations = load_json("launch.json")["configurations"]
    assert len(configurations) == 5
    for configuration in configurations:
        assert configuration["program"] == "${workspaceFolder}/bot.py"
        assert configuration["args"] == ["--tcp"]
        assert configuration.get("preLaunchTask", next(iter(labels))) in labels
