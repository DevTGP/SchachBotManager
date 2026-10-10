"""The messages to the viewer, checked against spec/protocol/viewer-v1/ (E106)."""

import pytest
from protocol_schemas import VIEWER, example, violations

import sbm
from sbm.viewer import messages

INFO = sbm.GameInfo(
    game_id="66f1c2a9e4b0a1b2c3d4e5f6",
    color=sbm.BLACK,
    opponent_name="Random",
    start_fen=sbm.Board().fen(),
    initial_time_ms=300000,
    increment_ms=2000,
    startup_ms=10000,
    memory_limit_mib=1024,
    discipline="Blitz",
)
AFTER_E4 = example("move.own", VIEWER)["fen"]


def check(message: dict) -> dict:
    assert violations("viewer_message", message, VIEWER) == []
    return message


def test_start():
    assert check(messages.start("Material", INFO)) == {
        "type": "start",
        "v": 1,
        "bot": "Material",
        "color": "black",
        "opponent": "Random",
        "start_fen": INFO.start_fen,
        "initial_time_ms": 300000,
        "increment_ms": 2000,
        "discipline": "Blitz",
    }


def test_start_without_discipline_and_with_a_long_name():
    info = sbm.GameInfo(**{**INFO.__dict__, "discipline": "", "color": sbm.WHITE})
    message = check(messages.start("B" * 100, info))
    assert "discipline" not in message
    assert message["bot"] == "B" * messages.MAX_NAME_LENGTH
    assert message["color"] == "white"


def test_move_with_clocks_and_info():
    info = {"depth": 3, "score_cp": 25, "pv": ["e2e4", "e7e5"]}
    message = check(messages.move(1, "e2e4", AFTER_E4, True, (299500, 300000), 500, info))
    assert message == example("move.own", VIEWER)


def test_move_without_clocks_and_negative_times():
    assert check(messages.move(1, "e2e4", AFTER_E4, False, None)) == {
        "type": "move",
        "ply": 1,
        "move": "e2e4",
        "fen": AFTER_E4,
        "by": "opponent",
    }
    message = check(messages.move(1, "e2e4", AFTER_E4, True, (-5, 10), -1))
    assert (message["white_ms"], message["black_ms"], message["elapsed_ms"]) == (0, 10, 0)


@pytest.mark.parametrize(
    ("level", "name"),
    [
        (sbm.TRACE, "debug"),
        (sbm.DEBUG, "debug"),
        (sbm.INFO, "info"),
        (sbm.WARN, "warn"),
        (sbm.ERROR, "error"),
    ],
)
def test_log_levels(level, name):
    assert check(messages.log(level, "12:00:00.250", "text"))["level"] == name


def test_log_is_shortened():
    message = check(messages.log(sbm.INFO, "12:00:00.250", "x" * 5000))
    assert len(message["text"]) == messages.MAX_LOG_LENGTH


def test_game_over_of_the_referee_is_a_viewer_message():
    check(example("game_over.with_final_position"))
