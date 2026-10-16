"""C# Material against the Python reference bots in the Python arena with its strict referee.

Over stdio against Python's material and over TCP against random (E198): every game ends by
the rules, ready names the language and the core version, and every C# move carries info.
"""

import re
import subprocess
import sys
from pathlib import Path

from sbm.arena.entrants import ProcessEntrant, TcpEntrant
from sbm.arena.series import Game, Series
from sbm.referee import MatchRecord, MatchSettings

ENDINGS = {
    "checkmate",
    "stalemate",
    "insufficient_material",
    "fifty_move_rule",
    "threefold_repetition",
    "max_moves",
}
CORE = Path(__file__).resolve().parents[3] / "core" / "CMakeLists.txt"
# The version ready reports is that of the core the C# bot runs on (E36).
CORE_VERSION = re.search(r"project\(sbm_core VERSION ([0-9.]+)", CORE.read_text()).group(1)
SETTINGS = MatchSettings(initial_time_ms=120_000, max_moves=100, game_id="cross")


def play(series: Series) -> list[MatchRecord]:
    records = []

    def on_end(game: Game, record: MatchRecord) -> None:
        records.append(record)

    series.play(on_end=on_end)
    return records


def check(record: MatchRecord) -> None:
    assert record.outcome.termination in ENDINGS, record.outcome
    sides = (record.white, record.black)
    csharp = [color for color, side in enumerate(sides) if side.lang == "csharp"]
    assert len(csharp) == 1, sides
    assert sides[csharp[0]].sdk == CORE_VERSION
    moves = record.moves[csharp[0] :: 2]
    assert moves
    for move in moves:
        assert move.info is not None, move
        assert move.info["depth"] == 2
        assert move.info["nodes"] > 0
        assert ("score_cp" in move.info) != ("score_mate" in move.info)


def test_against_python_material_over_stdio(csharp_material):
    csharp = ProcessEntrant("Material C#", csharp_material, sys.stderr)
    python = ProcessEntrant("Material Python", [sys.executable, "-m", "sbm.bots.material"], None)
    records = play(Series(csharp, python, SETTINGS, 2))
    assert [record.white.lang for record in records] == ["csharp", "python"]
    for record in records:
        check(record)


def test_against_random_over_tcp(csharp_material):
    csharp = TcpEntrant("Material C#", 0, lambda text: None)
    port = csharp._listener.port
    bot = subprocess.Popen([*csharp_material, "--tcp", str(port)])
    try:
        random = ProcessEntrant("Random", [sys.executable, "-m", "sbm.bots.random_mover"], None)
        (record,) = play(Series(random, csharp, SETTINGS, 1))
        assert record.black.lang == "csharp"
        check(record)
        assert bot.wait(timeout=30) == 0
    finally:
        csharp.close()
        if bot.poll() is None:
            bot.kill()
