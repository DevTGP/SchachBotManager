"""Publishes the moves of a running match to the gateway for its viewers (live-v1, E142).

A thread of its own talks to the gateway, so a slow or missing gateway never holds up the game:
move only queues the move. The feed keeps every move; after a broken connection it connects
again and sends open and all moves once more. The viewers then miss nothing, and without the
gateway they still see the moves through the API.
"""

import json
import logging
import queue
import socket
import threading
import time
from collections.abc import Callable

log = logging.getLogger(__name__)

# Opens a TCP connection: (address, timeout) -> socket, like socket.create_connection.
Connect = Callable[[tuple[str, int], float], socket.socket]

_END = object()


class LiveFeed:
    """Without an address (no SBM_LIVE_ADDRESS) every method does nothing."""

    def __init__(
        self,
        address: tuple[str, int] | None,
        match_id: object,
        *,
        connect: Connect = socket.create_connection,
        retry_seconds: float = 5.0,
        connect_timeout: float = 2.0,
        end_wait: float = 3.0,
    ) -> None:
        self._address = address
        self._match_id = str(match_id)
        self._connect = connect
        self._retry_seconds = retry_seconds
        self._connect_timeout = connect_timeout
        self._end_wait = end_wait
        self._queue: queue.Queue = queue.Queue()
        self._moves: list[bytes] = []
        self._thread: threading.Thread | None = None

    def open(self) -> None:
        if self._address is None or self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._run, name=f"live {self._match_id}", daemon=True
        )
        self._thread.start()

    def move(self, move: dict) -> None:
        """A move document as the API serves it (Move in openapi)."""
        if self._thread is not None:
            self._queue.put(move)

    def end(self) -> None:
        """Waits a moment for the gateway to get the last moves; the game is over anyway."""
        if self._thread is None:
            return
        self._queue.put(_END)
        self._thread.join(self._end_wait)
        self._thread = None

    def _run(self) -> None:
        connection: socket.socket | None = None
        next_attempt = 0.0
        try:
            while True:
                if connection is None and time.monotonic() >= next_attempt:
                    connection = self._open_connection()
                    if connection is None:
                        next_attempt = time.monotonic() + self._retry_seconds
                timeout = None
                if connection is None:
                    timeout = max(next_attempt - time.monotonic(), 0.0)
                try:
                    item = self._queue.get(timeout=timeout)
                except queue.Empty:
                    continue
                if item is _END:
                    if connection is not None:
                        self._send(connection, [_line({"type": "end"})])
                    return
                line = _line({"type": "move", "move": item})
                self._moves.append(line)
                if connection is not None and not self._send(connection, [line]):
                    connection.close()
                    connection = None
                    next_attempt = time.monotonic() + self._retry_seconds
        finally:
            if connection is not None:
                connection.close()

    def _open_connection(self) -> socket.socket | None:
        try:
            connection = self._connect(self._address, self._connect_timeout)
        except OSError as error:
            log.warning("live feed of match %s: gateway unreachable: %s", self._match_id, error)
            return None
        opening = _line({"type": "open", "v": 1, "match_id": self._match_id})
        if self._send(connection, [opening, *self._moves]):
            return connection
        connection.close()
        return None

    def _send(self, connection: socket.socket, lines: list[bytes]) -> bool:
        try:
            connection.sendall(b"".join(lines))
        except OSError as error:
            log.warning("live feed of match %s: connection lost: %s", self._match_id, error)
            return False
        return True


def _line(message: dict) -> bytes:
    return json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode() + b"\n"
