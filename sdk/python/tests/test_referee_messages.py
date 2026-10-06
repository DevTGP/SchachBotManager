"""Messages from the referee match the protocol schemas."""

from protocol_schemas import violations

from sbm import BLACK, WHITE
from sbm.referee import MatchSettings
from sbm.referee.referee_messages import error, game_over, init, turn


def test_init():
    settings = MatchSettings(initial_time_ms=60_000, increment_ms=500, game_id="a_1")
    message = init(settings, BLACK, "x" * 64)
    assert violations("init", message) == []
    assert message["color"] == "black"
    assert message["supported"] == [1]
    assert init(settings, WHITE, "B")["color"] == "white"


def test_turn():
    fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
    assert violations("turn", turn("e2e4", fen, 1, 0, 2**53 - 1)) == []
    assert violations("turn", turn(None, fen, 0, 5, 5)) == []


def test_error_message_is_cut():
    message = error("illegal_move", "x" * 5000)
    assert violations("error", message) == []
    assert len(message["message"]) == 1024


def test_game_over():
    assert violations("game_over", game_over("*", "startup_timeout")) == []
    assert violations("game_over", game_over("1/2-1/2", "max_moves")) == []
