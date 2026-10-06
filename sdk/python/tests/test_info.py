"""Info in the move message: limits of the protocol, truncation and dropped fields (E43, E63)."""

import pytest
from protocol_schemas import violations

import sbm
from sbm import protocol


def move_message(info: sbm.Info) -> dict:
    message = protocol.move("e2e4", info)
    assert violations("move", message) == []
    return message


def test_full_info():
    board = sbm.Board()
    pv = [board.parse_move("e2e4"), sbm.Move.parse("e7e5")]
    info = sbm.Info(depth=12, seldepth=18, score_cp=-35, nodes=1_534_211, pv=pv, text="book")
    assert move_message(info)["info"] == {
        "depth": 12,
        "seldepth": 18,
        "score_cp": -35,
        "nodes": 1_534_211,
        "pv": ["e2e4", "e7e5"],
        "text": "book",
    }


def test_empty_info():
    assert move_message(sbm.Info())["info"] == {}
    assert "info" not in protocol.move("e2e4", None)


def test_limits_are_inclusive(capsys):
    info = sbm.Info(depth=1024, seldepth=0, score_mate=-1024, nodes=2**53 - 1)
    assert move_message(info)["info"] == {
        "depth": 1024,
        "seldepth": 0,
        "score_mate": -1024,
        "nodes": 2**53 - 1,
    }
    assert move_message(sbm.Info(score_cp=100_000))["info"] == {"score_cp": 100_000}
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("depth", -1),
        ("depth", 1025),
        ("seldepth", 2.5),
        ("score_cp", -100_001),
        ("score_mate", 0),
        ("score_mate", 1025),
        ("nodes", 2**53),
        ("nodes", "many"),
    ],
)
def test_invalid_integers_are_left_out(capsys, name, value):
    assert move_message(sbm.Info(**{name: value, "text": "kept"}))["info"] == {"text": "kept"}
    assert f"WARN  report: {name}=" in capsys.readouterr().err


def test_both_scores_keep_mate(capsys):
    assert move_message(sbm.Info(score_cp=500, score_mate=3))["info"] == {"score_mate": 3}
    assert "only score_mate" in capsys.readouterr().err


def test_pv_is_truncated():
    moves = [sbm.Move.parse("g1f3"), sbm.Move.parse("f3g1")] * 20
    assert move_message(sbm.Info(pv=moves))["info"]["pv"] == ["g1f3", "f3g1"] * 16


@pytest.mark.parametrize("bad", [sbm.NULL_MOVE, sbm.RESIGN, "e2e4", None])
def test_pv_ends_before_a_move_without_uci(capsys, bad):
    moves = [sbm.Move.parse("e2e4"), bad, sbm.Move.parse("e7e5")]
    assert move_message(sbm.Info(pv=moves))["info"]["pv"] == ["e2e4"]
    assert "report: pv ends" in capsys.readouterr().err


def test_pv_that_is_no_list(capsys):
    assert move_message(sbm.Info(pv=5))["info"]["pv"] == []
    assert "not a list" in capsys.readouterr().err


def test_text_is_truncated_by_characters():
    text = "♞" * 300
    assert move_message(sbm.Info(text=text))["info"]["text"] == "♞" * 256


def test_text_without_utf8_form():
    assert move_message(sbm.Info(text="a\ud800b"))["info"]["text"] == "a?b"


def test_text_that_is_no_str(capsys):
    assert move_message(sbm.Info(text=7))["info"] == {}
    assert "text=7" in capsys.readouterr().err
