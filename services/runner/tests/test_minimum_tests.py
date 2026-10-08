"""The Mindesttests without nsjail: the positions, who is at fault, and one real test game."""

import sys

import pytest
import sbm
from sbm.referee import MatchRecord, MoveRecord, Outcome, SideRecord
from uploads import CheckedPlayer

from sbm_runner.players import plain_player
from sbm_runner.verification.minimum_tests import (
    MAX_STDERR_BYTES,
    POSITIONS,
    RANDOM,
    TEST_GAMES,
    _problem,
    play_test,
)


def board(name: str) -> sbm.Board:
    return sbm.Board.from_fen(POSITIONS[name])


def test_each_position_tests_its_rule():
    assert len(board("opening").legal_moves()) == 20
    assert board("check").is_check()
    assert any(move.is_promotion() for move in board("promotion").legal_moves())
    assert "e5f6" in [move.uci() for move in board("en_passant").legal_moves()]
    assert [move.uci() for move in board("only_move").legal_moves()] == ["h8h7"]


def test_the_bot_has_the_move_in_every_position():
    for game in TEST_GAMES:
        if game.settings.start_fen is not None and game.name.startswith("position_"):
            assert sbm.Board.from_fen(game.settings.start_fen).side_to_move() == game.color


def test_every_test_has_its_own_game_id():
    assert len({game.settings.game_id for game in TEST_GAMES}) == len(TEST_GAMES)


class Ended:
    def __init__(self, exited_cleanly: bool = True, stderr_bytes: int = 0) -> None:
        self.exited_cleanly = exited_cleanly
        self.stderr_bytes = stderr_bytes


def record(outcome: Outcome, fen: str = sbm.Board().fen()) -> MatchRecord:
    side = SideRecord(name="x", sdk="0", lang="python")
    move = MoveRecord(1, "e2e4", "e4", fen, 5, 9_995, None)
    return MatchRecord(start_fen=fen, white=side, black=side, moves=[move], outcome=outcome)


LOSS_ON_TIME = Outcome("0-1", "timeout", sbm.BLACK, "white ran out of time")
FLAG_DRAW = Outcome("1/2-1/2", "timeout_insufficient_material", None, "lone king")
WHITE_TO_MOVE = "8/8/8/8/8/8/8/K6k w - - 0 1"


def test_only_the_side_at_fault_fails():
    assert _problem(sbm.WHITE, record(LOSS_ON_TIME), Ended()) == "timeout: white ran out of time"
    assert _problem(sbm.BLACK, record(LOSS_ON_TIME), Ended()) is None
    checkmate = Outcome("1-0", "checkmate", sbm.WHITE, "")
    assert _problem(sbm.BLACK, record(checkmate), Ended()) is None


def test_a_flag_draw_fails_the_side_that_ran_out():
    assert _problem(sbm.WHITE, record(FLAG_DRAW, WHITE_TO_MOVE), Ended()) is not None
    assert _problem(sbm.BLACK, record(FLAG_DRAW, WHITE_TO_MOVE), Ended()) is None


def test_a_bot_must_exit_cleanly_and_log_little():
    draw = record(Outcome("1/2-1/2", "max_moves", None, ""))
    assert "exit with code 0" in _problem(sbm.WHITE, draw, Ended(exited_cleanly=False))
    assert "stderr" in _problem(sbm.WHITE, draw, Ended(stderr_bytes=MAX_STDERR_BYTES + 1))
    assert _problem(sbm.WHITE, draw, Ended(stderr_bytes=MAX_STDERR_BYTES)) is None


@pytest.mark.parametrize("name", ["position_promotion", "position_only_move"])
def test_a_real_test_game(name):
    game = next(game for game in TEST_GAMES if game.name == name)
    bot = CheckedPlayer("Material", [sys.executable, "-m", "sbm.bots.material"], log=None)

    result = play_test(game, bot, plain_player(RANDOM))

    assert result["passed"], result
    assert result["name"] == name
    assert result["color"] == ("white" if game.color == sbm.WHITE else "black")
    assert result["plies"] >= 1
