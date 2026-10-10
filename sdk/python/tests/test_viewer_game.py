"""A game reports its moves to an open viewer window (E106)."""

import pytest
from protocol_schemas import VIEWER, example, violations
from test_game import GAME_OVER, START, FirstMove, play, turn
from viewer_fakes import FakeProcess

import sbm
from sbm.viewer import window as window_module
from sbm.viewer.window import ViewerWindow


@pytest.fixture
def process(monkeypatch):
    process = FakeProcess()
    monkeypatch.setattr(window_module._State, "window", ViewerWindow(process))
    return process


def after(fen: str, *moves: str) -> str:
    board = sbm.Board.from_fen(fen)
    for uci in moves:
        board.make_move(board.parse_move(uci))
    return board.fen()


def test_game_as_white(process):
    first = sbm.Board().legal_moves()[0].uci()
    reply = sbm.Board.from_fen(after(START, first)).legal_moves()[0].uci()
    second_turn = turn(after(START, first, reply), 2, reply, remaining_ms=800)
    play(FirstMove(), example("init.standard"), example("turn.first_move"), second_turn, GAME_OVER)
    messages = process.messages()
    for message in messages:
        assert violations("viewer_message", message, VIEWER) == []
    assert [message["type"] for message in messages] == [
        "start",
        "move",
        "move",
        "move",
        "game_over",
    ]
    start, own, opponent, own_again, end = messages
    assert (start["bot"], start["color"], start["opponent"]) == (
        "FirstMove",
        "white",
        "Stockfisch Junior",
    )
    assert (own["ply"], own["move"], own["by"]) == (1, first, "bot")
    assert own["fen"] == after(START, first)
    assert own["black_ms"] == 300000
    assert own["white_ms"] <= 300000 + 2000
    assert own["elapsed_ms"] >= 0
    assert (opponent["ply"], opponent["move"], opponent["by"]) == (2, reply, "opponent")
    assert (opponent["white_ms"], opponent["black_ms"]) == (800, 2000)
    assert (own_again["ply"], own_again["by"]) == (3, "bot")
    assert end == GAME_OVER


def test_no_window_no_messages(monkeypatch):
    monkeypatch.setattr(window_module._State, "window", None)
    play(FirstMove(), example("init.standard"), example("turn.first_move"), GAME_OVER)


def test_resignation_is_not_a_move(process):
    class Resigns(sbm.Bot):
        def choose_move(self, board, clock):
            return sbm.Move.RESIGN

    play(Resigns(), example("init.standard"), example("turn.first_move"), GAME_OVER)
    assert [message["type"] for message in process.messages()] == ["start", "game_over"]
