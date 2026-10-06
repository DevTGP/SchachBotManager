"""The reference bots in sbm.bots."""

import subprocess
import sys

import pytest
from spec_files import SPEC

import sbm
from sbm.bot import take_report
from sbm.bots.material import MaterialBot, material
from sbm.bots.random_mover import RandomMover

CLOCK = sbm.Clock(60_000, 60_000, 0)


def choose(bot: sbm.Bot, fen: str) -> tuple[str, sbm.Info | None]:
    board = sbm.Board.from_fen(fen)
    move = bot.choose_move(board, CLOCK)
    assert board.fen() == fen  # every searched move is undone
    assert board.is_legal(move)
    return move.uci(), take_report(bot)


def test_random_mover_plays_every_legal_move():
    board = sbm.Board()
    moves = {RandomMover().choose_move(board, CLOCK).uci() for _ in range(400)}
    assert moves == {move.uci() for move in board.legal_moves()}


def test_material_counts_for_the_side_to_move():
    assert material(sbm.Board()) == 0
    assert material(sbm.Board.from_fen("4k3/8/8/8/8/8/8/R3K2Q w - - 0 1")) == 1400
    assert material(sbm.Board.from_fen("4k3/8/8/8/8/8/8/R3K2Q b - - 0 1")) == -1400


def test_takes_a_hanging_queen():
    uci, info = choose(MaterialBot(), "4k3/8/8/3q4/8/8/8/3RK3 w - - 0 1")
    assert uci == "d1d5"
    assert (info.depth, info.score_cp) == (2, 500)
    assert info.nodes > 0


def test_does_not_take_a_defended_pawn_with_the_queen():
    fen = "4k3/8/2p5/3p4/8/8/8/3QK3 w - - 0 1"
    for _ in range(10):
        uci, info = choose(MaterialBot(), fen)
        assert uci != "d1d5"
        assert info.score_cp == 700  # queen against two pawns


def test_mates_in_one():
    uci, info = choose(MaterialBot(), "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1")
    assert uci == "a1a8"
    assert info.score_mate == 1


def test_avoids_a_mate_in_one():
    # Nb3 allows Re1#; Nc2 guards e1, pawn and king moves make room for the king.
    fen = "4r1k1/5ppp/8/8/8/8/5PPP/N5K1 w - - 0 1"
    for _ in range(10):
        uci, info = choose(MaterialBot(), fen)
        assert uci != "a1b3"
        assert info.score_cp == 300 - 500


def test_equal_moves_are_chosen_at_random():
    moves = {choose(MaterialBot(), sbm.Board().fen())[0] for _ in range(30)}
    assert len(moves) > 5


@pytest.mark.parametrize("module", ["sbm.bots.random_mover", "sbm.bots.material"])
def test_runs_as_module(module):
    init = (SPEC / "protocol" / "v1" / "examples" / "valid" / "init.standard.json").read_text()
    done = subprocess.run(
        [sys.executable, "-m", module],
        input=init.strip() + "\n",
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert '"type":"ready"' in done.stdout.replace(" ", "")
