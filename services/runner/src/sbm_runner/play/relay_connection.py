"""The runner's end of one relay connection to the gateway (relay-v1, gateway.md).

One connection carries one seat of one game. A reader thread sorts what the gateway sends:
lines of the client go to a queue, present and absent tell whether a client holds the seat.
"""

import contextlib
import json
import queue
import socket
import threading
import time

from sbm.referee import PlayerTimeout

VERSION = 1
# A line message holds up to 65536 characters, escaped in JSON up to six bytes each.
LINE_LIMIT = 6 * 65_536 + 1024
# Waiting without a deadline wakes up this often to look at the client's presence.
WAKE_SECONDS = 0.25
# Closing waits this long for the gateway to take the last lines and end its side.
CLOSE_SECONDS = 2.0


class RelayClosed(Exception):
    """The gateway ended the connection or refused the seat; the game cannot go on."""


class SeatAbandoned(Exception):
    """The client stayed away longer than the grace period; the game is aborted."""


_END = object()


class RelayConnection:
    def __init__(self, address: tuple[str, int], match_id: str, seat_hash: str) -> None:
        self._address = address
        self._match_id = match_id
        self._seat_hash = seat_hash
        self._socket: socket.socket | None = None
        self._lines: queue.Queue = queue.Queue()
        self._present = threading.Event()
        self._absent_since: float | None = None
        self._closed_reason: str | None = None
        self._lock = threading.Lock()
        self._reader: threading.Thread | None = None

    def open(self, timeout: float) -> None:
        """Connects and attaches the seat; raises OSError if the gateway is unreachable."""
        self._socket = socket.create_connection(self._address, timeout)
        self._socket.settimeout(None)
        self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._write(
            {
                "type": "attach",
                "v": VERSION,
                "match_id": self._match_id,
                "seat_hash": self._seat_hash,
            }
        )
        self._reader = threading.Thread(
            target=self._read, name=f"relay {self._match_id}", daemon=True
        )
        self._reader.start()

    def wait_present(self, timeout: float) -> bool:
        """Whether a client took the seat within timeout seconds."""
        return self._present.wait(timeout)

    def send_line(self, data: str) -> None:
        try:
            self._write({"type": "line", "data": data})
        except OSError as error:
            raise RelayClosed(f"cannot write to the gateway: {error}") from None

    def receive(self, deadline_ns: int | None, absent_grace: float) -> str:
        """The next line of the client; raises PlayerTimeout at the deadline, RelayClosed, or
        SeatAbandoned when the client has been away longer than absent_grace seconds.
        """
        while True:
            try:
                item = self._lines.get(timeout=self._wait_seconds(deadline_ns))
            except queue.Empty:
                if deadline_ns is not None and time.monotonic_ns() >= deadline_ns:
                    raise PlayerTimeout() from None
                self._check_presence(absent_grace)
                continue
            if item is _END:
                self._lines.put(_END)
                raise RelayClosed(self._closed_reason or "the gateway closed the connection")
            return item

    def close(self) -> None:
        """Ends the own side first and reads until the gateway ends its side, so the last
        lines (game_over) are not lost to a reset; then closes. Safe to call twice.
        """
        if self._socket is None:
            return
        with contextlib.suppress(OSError):
            self._socket.shutdown(socket.SHUT_WR)
        if self._reader is not None and self._reader is not threading.current_thread():
            self._reader.join(CLOSE_SECONDS)
        with contextlib.suppress(OSError):
            self._socket.shutdown(socket.SHUT_RDWR)
        self._socket.close()

    def _wait_seconds(self, deadline_ns: int | None) -> float:
        if deadline_ns is None:
            return WAKE_SECONDS
        return max(0.0, min((deadline_ns - time.monotonic_ns()) / 1e9, WAKE_SECONDS))

    def _check_presence(self, absent_grace: float) -> None:
        absent_since = self._absent_since
        if absent_since is not None and time.monotonic() - absent_since > absent_grace:
            raise SeatAbandoned(f"the client was away for more than {absent_grace:.0f} s")

    def _write(self, message: dict) -> None:
        line = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode() + b"\n"
        with self._lock:
            self._socket.sendall(line)

    def _read(self) -> None:
        try:
            with self._socket.makefile("rb") as stream:
                while line := stream.readline(LINE_LIMIT):
                    if not self._handle(line):
                        break
        except (OSError, ValueError):
            pass
        self._present.clear()
        self._lines.put(_END)

    def _handle(self, line: bytes) -> bool:
        """False ends the reading."""
        try:
            message = json.loads(line)
            kind = message["type"]
        except (ValueError, TypeError, KeyError):
            self._closed_reason = "the gateway broke the relay protocol"
            return False
        if kind == "line" and isinstance(message.get("data"), str):
            self._lines.put(message["data"])
        elif kind == "present":
            self._absent_since = None
            self._present.set()
        elif kind == "absent":
            self._present.clear()
            self._absent_since = time.monotonic()
        elif kind == "refused":
            self._closed_reason = f"the gateway refused the seat: {message.get('code')}"
            return False
        else:
            self._closed_reason = f"the gateway sent an unknown message {kind!r}"
            return False
        return True
