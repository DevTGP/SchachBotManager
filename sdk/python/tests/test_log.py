"""Log: levels, line format and errors (spec/api/log.json)."""

import io
import re

import pytest

import sbm
from sbm import log

LINE = re.compile(r"^\d\d:\d\d:\d\d\.\d{3} \[ply (-|\d+)\] (TRACE|DEBUG|INFO |WARN |ERROR) (.*)$")


def lines(text: str) -> list[tuple[str, str, str]]:
    return [LINE.match(line).groups() for line in text.splitlines()]


def test_default_level_is_info(capsys):
    assert sbm.Log.level() == sbm.INFO
    for write in [sbm.Log.trace, sbm.Log.debug, sbm.Log.info, sbm.Log.warn, sbm.Log.error]:
        write(write.__name__)
    assert [level.strip() for _, level, _ in lines(capsys.readouterr().err)] == [
        "INFO",
        "WARN",
        "ERROR",
    ]


def test_writes_to_stderr_only(capsys):
    sbm.Log.error("message")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert lines(captured.err) == [("-", "ERROR", "message")]


def test_set_level_and_is_enabled(capsys):
    sbm.Log.set_level(sbm.TRACE)
    assert sbm.Log.level() == sbm.TRACE
    assert all(sbm.Log.is_enabled(level) for level in range(sbm.TRACE, sbm.OFF))
    assert not sbm.Log.is_enabled(sbm.OFF)
    sbm.Log.trace("visible")
    sbm.Log.set_level(sbm.OFF)
    assert not any(sbm.Log.is_enabled(level) for level in range(sbm.TRACE, sbm.OFF + 1))
    sbm.Log.error("hidden")
    assert lines(capsys.readouterr().err) == [("-", "TRACE", "visible")]


def test_level_errors():
    for function in [sbm.Log.set_level, sbm.Log.is_enabled]:
        with pytest.raises(sbm.InvalidArgumentError, match=function.__name__):
            function(6)
        with pytest.raises(sbm.InvalidArgumentError):
            function(-1)
        with pytest.raises(TypeError):
            function("debug")
    assert sbm.Log.level() == sbm.INFO


def test_ply_and_file(capsys):
    file = io.StringIO()
    log.configure(sbm.DEBUG, file)
    log.set_ply(12)
    sbm.Log.debug("two\nlines")
    sbm.Log.info(42)
    err = capsys.readouterr().err
    assert err == file.getvalue()
    assert err.splitlines()[0].endswith("[ply 12] DEBUG two")
    assert err.splitlines()[1] == "lines"
    assert err.splitlines()[2].endswith("[ply 12] INFO  42")


def test_log_is_not_instantiated():
    with pytest.raises(TypeError):
        sbm.Log()


def test_listener_receives_written_lines(capsys):
    received = []
    log.set_listener(lambda level, time, text: received.append((level, time, text)))
    try:
        sbm.Log.debug("hidden")
        sbm.Log.warn(42)
    finally:
        log.set_listener(None)
    sbm.Log.error("after")
    ((level, time, text),) = received
    assert (level, text) == (sbm.WARN, "42")
    assert re.fullmatch(r"\d\d:\d\d:\d\d\.\d{3}", time)
    assert lines(capsys.readouterr().err)[0][1:] == ("WARN ", "42")
