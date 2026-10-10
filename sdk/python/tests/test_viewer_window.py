"""The viewer window of a bot program, with a fake process instead of the viewer (E106)."""

import pytest
from protocol_schemas import VIEWER, example, violations
from test_viewer_messages import AFTER_E4, INFO
from viewer_fakes import FakeProcess

import sbm
from sbm import log
from sbm.viewer import window as window_module
from sbm.viewer.window import ViewerWindow, active_window, open_window


@pytest.fixture(autouse=True)
def no_window(monkeypatch):
    monkeypatch.setattr(window_module._State, "window", None)
    monkeypatch.setattr(window_module._State, "missing_reported", False)
    yield
    log.set_listener(None)


def test_clocks_follow_the_color_of_the_bot():
    process = FakeProcess()
    window = ViewerWindow(process)
    window.game_started("Material", INFO)  # black
    window.move_played(1, "e2e4", AFTER_E4, False, clocks=(300000, 299000))
    start, move = process.messages()
    assert start["color"] == "black"
    assert (move["white_ms"], move["black_ms"]) == (299000, 300000)
    for message in process.messages():
        assert violations("viewer_message", message, VIEWER) == []


def test_game_over_sends_the_final_move_first():
    process = FakeProcess()
    game_over = example("game_over.with_final_position")
    ViewerWindow(process).game_over(game_over)
    move, end = process.messages()
    assert move == {
        "type": "move",
        "ply": 7,
        "move": "h5f7",
        "fen": game_over["fen"],
        "by": "opponent",
    }
    assert end == game_over


def test_game_over_without_a_final_move():
    process = FakeProcess()
    game_over = example("game_over.aborted_before_first_move")
    ViewerWindow(process).game_over(game_over)
    assert process.messages() == [game_over]


def test_closed_window_stays_silent():
    process = FakeProcess(broken=True)
    window = ViewerWindow(process)
    window.game_started("Material", INFO)
    assert not window.is_open()
    process.stdin.broken = False
    window.log_line(sbm.INFO, "12:00:00.000", "lost")
    assert process.messages() == []


def test_ended_process_is_not_open():
    process = FakeProcess()
    window = ViewerWindow(process)
    process.returncode = 0
    assert not window.is_open()


def test_wait_until_closed_holds_the_program(capsys):
    process = FakeProcess()
    window = ViewerWindow(process)
    window.wait_until_closed()
    assert process.waited
    assert process.stdin.closed
    assert "the program ends when the viewer window is closed" in capsys.readouterr().err


def test_missing_program_is_reported_once(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(window_module, "program_path", lambda: tmp_path / "sbm-viewer")
    assert open_window() is None
    assert open_window() is None
    assert capsys.readouterr().err.count("no window opens") == 1
    assert active_window() is None


def test_open_window_feeds_the_log(monkeypatch, tmp_path):
    program = tmp_path / "sbm-viewer"
    program.write_bytes(b"")
    process = FakeProcess()
    exits = []
    monkeypatch.setattr(window_module, "program_path", lambda: program)
    monkeypatch.setattr(window_module, "start_process", lambda path: process)
    monkeypatch.setattr(window_module.atexit, "register", exits.append)
    window = open_window()
    assert open_window() is window
    assert active_window() is window
    assert exits == [window.wait_until_closed]
    sbm.Log.warn("careful")
    sbm.Log.debug("not written at level INFO")
    (line,) = process.messages()
    assert (line["type"], line["level"], line["text"]) == ("log", "warn", "careful")
    assert violations("viewer_message", line, VIEWER) == []


def test_unstartable_program_is_reported(monkeypatch, tmp_path, capsys):
    program = tmp_path / "sbm-viewer"
    program.write_bytes(b"")

    def refuse(path):
        raise PermissionError("not executable")

    monkeypatch.setattr(window_module, "program_path", lambda: program)
    monkeypatch.setattr(window_module, "start_process", refuse)
    assert open_window() is None
    assert "cannot start sbm-viewer" in capsys.readouterr().err


def test_a_warning_while_sending_does_not_recurse(monkeypatch):
    process = FakeProcess()
    window = ViewerWindow(process)
    log.set_listener(window.log_line)
    real_encode = window_module.encode

    def encode_and_warn(message):
        sbm.Log.warn("written while sending")
        return real_encode(message)

    monkeypatch.setattr(window_module, "encode", encode_and_warn)
    window.log_line(sbm.INFO, "12:00:00.000", "first")
    assert [message["text"] for message in process.messages()] == ["first"]
