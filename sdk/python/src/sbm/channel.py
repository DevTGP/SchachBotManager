"""Line channel to the referee: one JSON message per line (NDJSON) over stdio or TCP."""

import json
import os
import socket
import sys
from typing import BinaryIO

MAX_LINE_BYTES = 65_536


class ProtocolError(Exception):
    """The referee sent something the protocol does not allow; the SDK cannot continue."""


class Channel:
    """Reads referee messages and writes bot messages, each flushed at once."""

    def __init__(self, reader: BinaryIO, writer: BinaryIO, closing: object = None) -> None:
        self._reader = reader
        self._writer = writer
        self._closing = closing

    def receive(self) -> dict | None:
        """The next message, or None at the end of the input."""
        line = self._reader.readline(MAX_LINE_BYTES + 2)
        if not line:
            return None
        content = line.removesuffix(b"\n").removesuffix(b"\r")
        if len(content) > MAX_LINE_BYTES:
            raise ProtocolError(f"line longer than {MAX_LINE_BYTES} bytes")
        try:
            message = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ProtocolError(f"invalid JSON: {error}") from None
        if not isinstance(message, dict):
            raise ProtocolError(f"message is not a JSON object: {content[:80]!r}")
        return message

    def send(self, message: dict) -> None:
        line = json.dumps(message, ensure_ascii=False, separators=(",", ":"))
        self._writer.write(line.encode("utf-8") + b"\n")
        self._writer.flush()

    def close(self) -> None:
        for stream in (self._writer, self._reader, self._closing):
            if stream is not None:
                stream.close()

    def __enter__(self) -> "Channel":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def open_stdio() -> Channel:
    """Takes stdin and stdout for the protocol and points file descriptors 0 and 1 elsewhere.

    Output of print or of native code then goes to stderr and reads from stdin see end of
    input, so nothing else can corrupt the protocol stream (bot-protokoll.md).
    """
    sys.stdout.flush()
    reader = os.fdopen(os.dup(0), "rb")
    writer = os.fdopen(os.dup(1), "wb")
    os.dup2(2, 1)
    null = os.open(os.devnull, os.O_RDONLY)
    os.dup2(null, 0)
    os.close(null)
    return Channel(reader, writer)


def open_tcp(port: int) -> Channel:
    """Connects to the waiting arena on this machine (local debugging only)."""
    connection = socket.create_connection(("127.0.0.1", port))
    connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    return Channel(connection.makefile("rb"), connection.makefile("wb"), connection)
