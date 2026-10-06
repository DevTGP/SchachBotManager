"""A bot started by the developer, e.g. in an IDE with breakpoints, that connects over TCP.

The arena listens on 127.0.0.1 only. The bot connects before the game starts, so the time the
developer needs to start it does not count against the startup budget; a bot plays one game
per process, so each game waits for a new connection. A TCP bot is never frozen.
"""

import contextlib
import socket
import sys
from collections.abc import Callable

from sbm.arena.stream_player import StreamPlayer

HOST = "127.0.0.1"
# Waiting for a connection wakes up this often, so Ctrl+C works on Windows too.
WAKE_SECONDS = 0.25


class TcpListener:
    """Port 0 picks a free port; port then holds the one in use."""

    def __init__(self, port: int) -> None:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            if sys.platform == "win32":
                self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            else:
                self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind((HOST, port))
            self._socket.listen(1)
            self.port = self._socket.getsockname()[1]
            self._socket.settimeout(WAKE_SECONDS)
        except OSError:
            self._socket.close()
            raise

    def accept(self) -> socket.socket:
        """Waits without a limit for the next connection."""
        while True:
            try:
                connection, _ = self._socket.accept()
            except TimeoutError:
                continue
            connection.settimeout(None)
            connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            return connection

    def close(self) -> None:
        self._socket.close()


class TcpPlayer(StreamPlayer):
    def __init__(self, name: str, connection: socket.socket) -> None:
        super().__init__(name)
        self._connection = connection
        self._attach(connection.makefile("rb"), connection.makefile("wb"))

    def close(self) -> None:
        # The bot reads game_over and the end of the connection, then ends on its own.
        with contextlib.suppress(OSError, ValueError):
            self._writer.close()
        with contextlib.suppress(OSError):
            self._connection.shutdown(socket.SHUT_RDWR)
        self._connection.close()


def connect(name: str, listener: TcpListener, announce: Callable[[str], None]) -> TcpPlayer:
    announce(f"waiting for {name} to connect on {HOST}:{listener.port}, e.g. --tcp {listener.port}")
    return TcpPlayer(name, listener.accept())
