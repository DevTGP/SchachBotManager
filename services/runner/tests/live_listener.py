"""A stand-in for the gateway's live port: accepts connections and keeps the lines of each."""

import json
import socket
import threading
import time


class LiveListener:
    def __init__(self) -> None:
        self._server = socket.create_server(("127.0.0.1", 0))
        self.address = self._server.getsockname()[:2]
        self.connections: list[list[dict]] = []
        self._threads: list[threading.Thread] = []
        self._accepting = threading.Thread(target=self._accept, daemon=True)
        self._accepting.start()

    def _accept(self) -> None:
        while True:
            try:
                connection, _peer = self._server.accept()
            except OSError:
                return
            lines: list[dict] = []
            self.connections.append(lines)
            thread = threading.Thread(target=self._read, args=(connection, lines), daemon=True)
            self._threads.append(thread)
            thread.start()

    def _read(self, connection: socket.socket, lines: list[dict]) -> None:
        with connection, connection.makefile("rb") as stream:
            for line in stream:
                lines.append(json.loads(line))

    def wait_closed(self, count: int = 1, seconds: float = 10) -> None:
        """Until count connections came and every one of them has ended."""
        deadline = time.monotonic() + seconds
        while len(self._threads) < count:
            assert time.monotonic() < deadline, "too few live connections"
            time.sleep(0.01)
        for thread in list(self._threads):
            thread.join(max(deadline - time.monotonic(), 0))
            assert not thread.is_alive(), "a live connection is still open"

    def close(self) -> None:
        self._server.close()
