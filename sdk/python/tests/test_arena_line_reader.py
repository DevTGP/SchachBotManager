"""Reading lines with a deadline from a bot's output."""

import io
import os
import time

import pytest

from sbm.arena.line_reader import LineReader
from sbm.referee import LineTooLong, PlayerClosed, PlayerTimeout
from sbm.referee.player import MAX_LINE_BYTES


def in_ms(milliseconds: int) -> int:
    return time.monotonic_ns() + milliseconds * 1_000_000


def test_lines_then_end():
    reader = LineReader(io.BytesIO(b'{"a":1}\r\n\nlast'), "bot")
    assert reader.receive(None) == b'{"a":1}'
    assert reader.receive(in_ms(1000)) == b""
    assert reader.receive(None) == b"last"
    for _ in range(2):
        with pytest.raises(PlayerClosed):
            reader.receive(None)


def test_too_long_line():
    reader = LineReader(
        io.BytesIO(b"x" * MAX_LINE_BYTES + b"\n" + b"y" * (MAX_LINE_BYTES + 1)), "b"
    )
    assert reader.receive(None) == b"x" * MAX_LINE_BYTES
    for _ in range(2):
        with pytest.raises(LineTooLong):
            reader.receive(None)


def test_timeout_and_late_line():
    read_end, write_end = os.pipe()
    with open(read_end, "rb") as stream, open(write_end, "wb") as writer:
        reader = LineReader(stream, "bot")
        started = time.monotonic()
        with pytest.raises(PlayerTimeout):
            reader.receive(in_ms(50))
        assert 0.04 <= time.monotonic() - started < 1
        with pytest.raises(PlayerTimeout):
            reader.receive(in_ms(-10))
        writer.write(b"late\n")
        writer.flush()
        assert reader.receive(in_ms(2000)) == b"late"
        writer.close()
        with pytest.raises(PlayerClosed):
            reader.receive(in_ms(2000))
