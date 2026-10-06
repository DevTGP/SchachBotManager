"""Reads protocol lines from a bot in a background thread, so the referee can wait with a
deadline on pipes and sockets alike (Windows pipes cannot be polled).
"""

import queue
import threading
import time
from typing import BinaryIO

from sbm.referee import LineTooLong, PlayerClosed, PlayerTimeout
from sbm.referee.player import MAX_LINE_BYTES

# Waiting without a deadline wakes up this often, so Ctrl+C works on Windows too.
WAKE_SECONDS = 0.25

_END = object()


class LineReader:
    """Lines without their line end, in order; the end of the stream and a too long line end
    the reading.
    """

    def __init__(self, stream: BinaryIO, name: str) -> None:
        self._stream = stream
        self._lines: queue.Queue = queue.Queue()
        self._thread = threading.Thread(target=self._read, name=f"read {name}", daemon=True)
        self._thread.start()

    def _read(self) -> None:
        try:
            while True:
                line = self._stream.readline(MAX_LINE_BYTES + 2)
                if not line:
                    break
                content = line.removesuffix(b"\n").removesuffix(b"\r")
                if len(content) > MAX_LINE_BYTES:
                    self._lines.put(LineTooLong())
                    return
                self._lines.put(content)
        except (OSError, ValueError):
            pass  # closed while reading: the same as the end of the stream
        self._lines.put(_END)

    def receive(self, deadline_ns: int | None) -> bytes:
        """The next line; raises PlayerTimeout, PlayerClosed at the end, or LineTooLong."""
        while True:
            if deadline_ns is None:
                timeout = WAKE_SECONDS
            else:
                timeout = min((deadline_ns - time.monotonic_ns()) / 1e9, WAKE_SECONDS)
            try:
                item = self._lines.get(timeout=timeout) if timeout > 0 else self._lines.get_nowait()
            except queue.Empty:
                if deadline_ns is not None and time.monotonic_ns() >= deadline_ns:
                    raise PlayerTimeout() from None
                continue
            if item is _END:
                self._lines.put(_END)  # every later call sees the end, too
                raise PlayerClosed("the bot closed its output")
            if isinstance(item, LineTooLong):
                self._lines.put(item)
                raise LineTooLong(f"a line is longer than {MAX_LINE_BYTES} bytes")
            return item
