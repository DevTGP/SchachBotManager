"""Line channel: NDJSON framing, line limit and malformed input."""

import io
import json

import pytest

from sbm.channel import MAX_LINE_BYTES, Channel, ProtocolError


def channel(data: bytes) -> tuple[Channel, io.BytesIO]:
    writer = io.BytesIO()
    return Channel(io.BytesIO(data), writer), writer


def test_receives_lines_until_end():
    reader, _ = channel(b'{"type":"a"}\n{"type":"b","x":[1]}\r\n{"type":"c"}')
    assert reader.receive() == {"type": "a"}
    assert reader.receive() == {"type": "b", "x": [1]}
    assert reader.receive() == {"type": "c"}
    assert reader.receive() is None


def test_line_limit():
    text = "x" * (MAX_LINE_BYTES - len('{"t":""}'))
    longest = json.dumps({"t": text}, separators=(",", ":")).encode()
    assert len(longest) == MAX_LINE_BYTES
    reader, _ = channel(longest + b"\n" + longest[:-1] + b'x"}\n')
    assert reader.receive() == {"t": text}
    with pytest.raises(ProtocolError, match="longer"):
        reader.receive()


@pytest.mark.parametrize("line", [b"{", b"[1, 2]", b'"text"', b"\xff\xfe", b"{} {}"])
def test_malformed_lines(line):
    reader, _ = channel(line + b"\n")
    with pytest.raises(ProtocolError):
        reader.receive()


def test_send_writes_one_compact_utf8_line():
    writer_channel, writer = channel(b"")
    writer_channel.send({"type": "move", "v": 1, "info": {"text": "Läufer\nopfer ♗"}})
    writer_channel.send({"type": "resign", "v": 1})
    lines = writer.getvalue().split(b"\n")
    assert lines[0] == '{"type":"move","v":1,"info":{"text":"Läufer\\nopfer ♗"}}'.encode()
    assert lines[1:] == [b'{"type":"resign","v":1}', b""]
