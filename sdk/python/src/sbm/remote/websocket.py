"""A small WebSocket client (RFC 6455) on the standard library: text messages, ping and close.

A reader thread answers pings at once, also while the bot thinks, and queues text messages; a
bot that is not reading would otherwise be dropped by the gateway's keep-alive.
"""

import base64
import contextlib
import hashlib
import os
import queue
import socket
import ssl
import struct
import threading
from urllib.parse import urlsplit

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
MAX_MESSAGE_BYTES = 4 * 65_536 + 1024
MAX_HEADER_BYTES = 16_384
TEXT, BINARY, CLOSE, PING, PONG, CONTINUATION = 0x1, 0x2, 0x8, 0x9, 0xA, 0x0

_CLOSED = object()


class WebSocketError(OSError):
    """The handshake failed or the server broke the protocol."""


class WebSocket:
    def __init__(self, connection: socket.socket) -> None:
        self._connection = connection
        self._reader = connection.makefile("rb")
        self._lock = threading.Lock()
        self._messages: queue.Queue = queue.Queue()
        self.close_code: int | None = None
        self._thread = threading.Thread(target=self._read_frames, name="websocket", daemon=True)

    @classmethod
    def connect(cls, url: str, timeout: float = 10.0) -> "WebSocket":
        """Opens ws:// or wss:// and does the opening handshake."""
        parts = urlsplit(url)
        if parts.scheme not in ("ws", "wss") or not parts.hostname:
            raise WebSocketError(f"not a WebSocket URL: {url}")
        secure = parts.scheme == "wss"
        port = parts.port or (443 if secure else 80)
        connection = socket.create_connection((parts.hostname, port), timeout)
        try:
            if secure:
                context = ssl.create_default_context()
                connection = context.wrap_socket(connection, server_hostname=parts.hostname)
            connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            client = cls(connection)
            client._handshake(parts, timeout)
        except BaseException:
            connection.close()
            raise
        connection.settimeout(None)
        client._thread.start()
        return client

    def _handshake(self, parts, timeout: float) -> None:
        key = base64.b64encode(os.urandom(16)).decode()
        host = parts.hostname if parts.port is None else f"{parts.hostname}:{parts.port}"
        path = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
        request = (
            f"GET {path} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n"
            "User-Agent: schachbotmanager\r\n\r\n"
        )
        self._connection.settimeout(timeout)
        self._connection.sendall(request.encode("ascii"))
        status, headers = self._read_response()
        if status != 101:
            raise WebSocketError(f"the server answered {status} instead of switching to WebSocket")
        digest = hashlib.sha1((key + GUID).encode("ascii")).digest()
        if headers.get("sec-websocket-accept") != base64.b64encode(digest).decode():
            raise WebSocketError("the server's handshake does not match")

    def _read_response(self) -> tuple[int, dict[str, str]]:
        lines, size = [], 0
        while True:
            line = self._reader.readline(MAX_HEADER_BYTES)
            size += len(line)
            if not line or size > MAX_HEADER_BYTES:
                raise WebSocketError("the server's handshake is incomplete")
            if line in (b"\r\n", b"\n"):
                break
            lines.append(line.decode("latin-1").strip())
        try:
            status = int(lines[0].split()[1])
        except (IndexError, ValueError):
            raise WebSocketError(f"not an HTTP answer: {lines[:1]}") from None
        headers = {}
        for line in lines[1:]:
            name, _, value = line.partition(":")
            headers[name.strip().lower()] = value.strip()
        return status, headers

    # Sending

    def send_text(self, text: str) -> None:
        self._send_frame(TEXT, text.encode("utf-8"))

    def close(self, code: int = 1000) -> None:
        """Starts the closing handshake; waits briefly for the reader to finish."""
        with contextlib.suppress(OSError):
            self._send_frame(CLOSE, struct.pack("!H", code))
        if self._thread.is_alive():
            self._thread.join(2.0)
        for stream in (self._reader, self._connection):
            with contextlib.suppress(OSError):
                stream.close()

    def _send_frame(self, opcode: int, payload: bytes) -> None:
        mask = os.urandom(4)
        length = len(payload)
        if length < 126:
            header = struct.pack("!BB", 0x80 | opcode, 0x80 | length)
        elif length < 65_536:
            header = struct.pack("!BBH", 0x80 | opcode, 0x80 | 126, length)
        else:
            header = struct.pack("!BBQ", 0x80 | opcode, 0x80 | 127, length)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        with self._lock:
            self._connection.sendall(header + mask + masked)

    # Receiving

    def receive_text(self, timeout: float | None = None) -> str | None:
        """The next text message, None once the connection is closed; queue.Empty on timeout."""
        item = self._messages.get(timeout=timeout)
        if item is _CLOSED:
            self._messages.put(_CLOSED)
            return None
        return item

    def _read_frames(self) -> None:
        parts: list[bytes] = []
        try:
            while True:
                final, opcode, payload = self._read_frame()
                if opcode == PING:
                    self._send_frame(PONG, payload)
                elif opcode == CLOSE:
                    if len(payload) >= 2:
                        self.close_code = struct.unpack("!H", payload[:2])[0]
                    with contextlib.suppress(OSError):
                        self._send_frame(CLOSE, payload[:2])
                    break
                elif opcode in (TEXT, CONTINUATION):
                    parts.append(payload)
                    if final:
                        self._messages.put(b"".join(parts).decode("utf-8"))
                        parts = []
                elif opcode == BINARY:
                    raise WebSocketError("binary messages are not part of the protocol")
        except (OSError, ValueError, UnicodeDecodeError):
            pass
        self._messages.put(_CLOSED)

    def _read_frame(self) -> tuple[bool, int, bytes]:
        first, second = self._read_exact(2)
        final = bool(first & 0x80)
        opcode = first & 0x0F
        length = second & 0x7F
        if length == 126:
            (length,) = struct.unpack("!H", self._read_exact(2))
        elif length == 127:
            (length,) = struct.unpack("!Q", self._read_exact(8))
        if length > MAX_MESSAGE_BYTES:
            raise WebSocketError("message too large")
        mask = self._read_exact(4) if second & 0x80 else None
        payload = self._read_exact(length)
        if mask is not None:
            payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        return final, opcode, payload

    def _read_exact(self, size: int) -> bytes:
        data = self._reader.read(size)
        if len(data) != size:
            raise WebSocketError("the connection ended in the middle of a frame")
        return data
