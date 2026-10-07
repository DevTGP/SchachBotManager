"""Reads a bot's stderr to the end and keeps only its last bytes for the runner's log."""

import contextlib
import threading
from typing import BinaryIO

from sbm_runner.sandbox.limits import STDERR_TAIL_BYTES

_CHUNK_BYTES = 4096


class StderrTail:
    """Reading keeps the pipe empty, so a bot that floods stderr never blocks on it."""

    def __init__(self, stream: BinaryIO, name: str, limit: int = STDERR_TAIL_BYTES) -> None:
        self._stream = stream
        self._limit = limit
        self._tail = bytearray()
        self._thread = threading.Thread(target=self._read, name=f"stderr {name}", daemon=True)
        self._thread.start()

    def _read(self) -> None:
        with contextlib.suppress(OSError, ValueError):
            while chunk := self._stream.read1(_CHUNK_BYTES):
                self._tail += chunk
                del self._tail[: -self._limit]

    def text(self, wait_seconds: float) -> str:
        """The tail after the stream has ended, or what has arrived within wait_seconds."""
        self._thread.join(wait_seconds)
        return bytes(self._tail).decode("utf-8", "replace")
