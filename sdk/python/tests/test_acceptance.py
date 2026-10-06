"""Acceptance of M1 (roadmap.md): two Python bots play by the rules through sbm-arena.

Every game runs real bot processes, as a bot author would start them, and ends by checkmate or
draw, time forfeit, illegal move or crash.
"""

import pytest
from arena_bots import CRASH_AFTER_READY, FIRST_MOVE, write_bot

from sbm.arena.cli import main

# Sleeps longer than its whole clock.
TOO_SLOW = """
import time
import sbm

class TooSlow(sbm.Bot):
    def choose_move(self, board, clock):
        time.sleep(1)
        return board.legal_moves()[0]

sbm.run(TooSlow)
"""

# Speaks the protocol by hand, since the SDK never sends an illegal move.
ILLEGAL_MOVE = """
import json, sys

for line in sys.stdin:
    message = json.loads(line)
    if message["type"] == "init":
        reply = {"type": "ready", "v": 1, "sdk": "0.0.0", "lang": "python"}
    elif message["type"] == "turn":
        reply = {"type": "move", "v": 1, "move": "e2e5"}
    else:
        break
    print(json.dumps(reply), flush=True)
"""


def play(argv: list[str], capsys) -> str:
    assert main([*argv, "--quiet"]) == 0
    return capsys.readouterr().out


def test_full_game_between_the_reference_bots(capsys):
    out = play(["material", "random", "--time", "30+0"], capsys)
    endings = ["1-0 checkmate", "1/2-1/2 stalemate", "1/2-1/2 threefold_repetition"]
    endings += ["1/2-1/2 fifty_move_rule", "1/2-1/2 insufficient_material"]
    assert any(ending in out for ending in endings), out


@pytest.mark.parametrize(
    ("source", "argv", "ending"),
    [
        (TOO_SLOW, ["--time", "0.2+0"], "0-1 timeout"),
        (ILLEGAL_MOVE, [], "0-1 illegal_move"),
        (CRASH_AFTER_READY, [], "0-1 crash"),
    ],
)
def test_white_loses_by(tmp_path, capsys, source, argv, ending):
    white = write_bot(tmp_path, "white", source)
    black = write_bot(tmp_path, "black", FIRST_MOVE)
    out = play([str(white), str(black), *argv], capsys)
    assert ending in out, out
