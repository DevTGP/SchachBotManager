"""The viewer as an argument of run and play, and SBM_NO_VIEWER (E108)."""

import sys

import pytest
from viewer_fakes import FakeProcess

import sbm
from sbm import log, runtime
from sbm.viewer import window as window_module
from sbm.viewer.window import DISABLE_VARIABLE, open_window


class First(sbm.Bot):
    def choose_move(self, board, clock):
        return board.legal_moves()[0]


@pytest.fixture(autouse=True)
def no_window(monkeypatch):
    monkeypatch.delenv(DISABLE_VARIABLE, raising=False)
    monkeypatch.setattr(window_module._State, "window", None)
    monkeypatch.setattr(window_module._State, "missing_reported", False)
    yield
    log.set_listener(None)


@pytest.fixture
def fake_viewer(monkeypatch, tmp_path):
    """open_window starts a fake process instead of the program and registers nothing."""
    program = tmp_path / "sbm-viewer"
    program.write_bytes(b"")
    process = FakeProcess()
    monkeypatch.setattr(window_module, "program_path", lambda: program)
    monkeypatch.setattr(window_module, "start_process", lambda path: process)
    monkeypatch.setattr(window_module.atexit, "register", lambda function: None)
    return process


def test_sbm_no_viewer_keeps_the_window_shut(monkeypatch, fake_viewer, capsys):
    monkeypatch.setenv(DISABLE_VARIABLE, "1")
    assert open_window() is None
    assert fake_viewer.messages() == []
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize("viewer", [False, True])
def test_run_opens_the_window_before_the_game(monkeypatch, viewer):
    events = []
    monkeypatch.setattr(sys, "argv", ["bot.py"])
    monkeypatch.setattr(runtime, "open_window", lambda: events.append("window"))
    monkeypatch.setattr(runtime, "_play", lambda bot, options: events.append("game"))
    sbm.run(First, viewer=viewer)
    assert events == (["window", "game"] if viewer else ["game"])


def test_play_shows_every_game_in_one_window(fake_viewer):
    sbm.play(First, "random", color="white", time="5+0", games=2, viewer=True)
    types = [message["type"] for message in fake_viewer.messages() if message["type"] != "log"]
    assert types.count("start") == 2
    assert types.count("game_over") == 2
    assert types[0] == "start"
    assert types[-1] == "game_over"


def test_play_without_viewer_opens_nothing(fake_viewer):
    sbm.play(First, "random", color="white", time="5+0")
    assert fake_viewer.messages() == []


def test_viewer_must_be_a_bool():
    with pytest.raises(TypeError, match="viewer must be True or False"):
        sbm.run(First, viewer="yes")
    with pytest.raises(TypeError, match="viewer must be True or False"):
        sbm.play(First, "random", viewer=1)
