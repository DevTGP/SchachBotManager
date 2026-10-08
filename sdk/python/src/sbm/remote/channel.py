"""The remote game as a channel of referee messages, like stdio or TCP for Game (E116)."""

import json
import queue

from sbm.channel import ProtocolError
from sbm.remote.game_request import RemoteError, Seat
from sbm.remote.websocket import WebSocket

JOIN_SECONDS = 45


class RemoteChannel:
    def __init__(self, socket: WebSocket) -> None:
        self._socket = socket

    @classmethod
    def join(cls, seat: Seat) -> "RemoteChannel":
        """Connects and takes the seat; raises RemoteError if the gateway refuses it."""
        socket = WebSocket.connect(seat.socket_url)
        socket.send_text(
            json.dumps({"type": "join", "v": 1, "match_id": seat.match_id, "seat": seat.seat})
        )
        try:
            answer = socket.receive_text(JOIN_SECONDS)
        except queue.Empty:
            socket.close()
            raise RemoteError("the game did not start in time", "no_game") from None
        message = _object(answer) if answer is not None else None
        if message is None or message.get("type") != "joined":
            socket.close()
            code = message.get("code", "no_game") if message else "no_game"
            raise RemoteError(f"the server refused the seat ({code})", str(code))
        return cls(socket)

    def receive(self) -> dict | None:
        text = self._socket.receive_text()
        return None if text is None else _object(text)

    def send(self, message: dict) -> None:
        self._socket.send_text(json.dumps(message, ensure_ascii=False, separators=(",", ":")))

    def close(self) -> None:
        self._socket.close()

    def __enter__(self) -> "RemoteChannel":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _object(text: str) -> dict:
    try:
        message = json.loads(text)
    except json.JSONDecodeError as error:
        raise ProtocolError(f"invalid JSON: {error}") from None
    if not isinstance(message, dict):
        raise ProtocolError(f"message is not a JSON object: {text[:80]!r}")
    return message
