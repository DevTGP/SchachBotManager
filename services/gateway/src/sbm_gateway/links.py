"""The two ends a session connects: the client's WebSocket and the runner's relay connection."""

import asyncio
import contextlib
import logging

from websockets.asyncio.server import ServerConnection
from websockets.exceptions import ConnectionClosed

from sbm_gateway import messages

log = logging.getLogger(__name__)

# Close codes of the WebSocket (gateway.md).
CLOSE_GAME_OVER = 1000
CLOSE_GOING_AWAY = 1001
CLOSE_REFUSED = 1008

# Closing waits for the client's answer; it runs in the background so no session waits for it.
_closing: set[asyncio.Task] = set()


def _in_background(coroutine) -> None:
    task = asyncio.create_task(coroutine)
    _closing.add(task)
    task.add_done_callback(_closing.discard)


class ClientGone(Exception):
    """The client's connection closed while the gateway wrote to it."""


class SocketClient:
    def __init__(self, socket: ServerConnection) -> None:
        self.socket = socket

    async def send(self, text: str) -> None:
        try:
            await self.socket.send(text)
        except ConnectionClosed:
            raise ClientGone() from None

    async def refuse(self, code: str, text: str, *, wait: bool = False) -> None:
        """Sends refused and closes the connection; without wait the closing handshake runs in
        the background. The connection's own handler waits, since returning closes it with 1000.
        """
        with contextlib.suppress(ConnectionClosed):
            await self.socket.send(messages.refused_client(code, text))
        close_code = CLOSE_GOING_AWAY if code == "shutdown" else CLOSE_REFUSED
        closing = self.socket.close(close_code, code)
        if wait:
            await closing
        else:
            _in_background(closing)

    def end(self, reason: str) -> None:
        """Closes the connection after the lines already sent, e.g. after game_over."""
        _in_background(self.socket.close(CLOSE_GAME_OVER, reason))


class RelayLink:
    def __init__(self, writer: asyncio.StreamWriter) -> None:
        self._writer = writer

    async def send(self, line: bytes) -> None:
        """Errors are ignored: a broken relay shows up as the end of its input."""
        if self._writer.is_closing():
            return
        self._writer.write(line)
        with contextlib.suppress(ConnectionError):
            await self._writer.drain()

    def close(self) -> None:
        self._writer.close()
