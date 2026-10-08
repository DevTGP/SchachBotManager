"""A side reached through the gateway that speaks the bot protocol v1 itself: a remote bot.

Its lines pass unchanged; the referee checks them as those of any bot. It is never frozen. A
side that stays away or loses the gateway raises an infrastructure error, so the game is
aborted without a result instead of scored (E113).
"""

import json

from sbm.referee import LineTooLong, Player
from sbm.referee.player import MAX_LINE_BYTES

from sbm_runner.play.relay_connection import RelayConnection


class RelayPlayer(Player):
    def __init__(self, name: str, connection: RelayConnection, *, absent_grace: float) -> None:
        super().__init__(name)
        self._connection = connection
        self._absent_grace = absent_grace

    def send(self, message: dict) -> None:
        self._connection.send_line(json.dumps(message, ensure_ascii=False, separators=(",", ":")))

    def receive(self, deadline_ns: int | None) -> bytes:
        line = self._connection.receive(deadline_ns, self._absent_grace).encode()
        if len(line) > MAX_LINE_BYTES:
            raise LineTooLong(f"a line is longer than {MAX_LINE_BYTES} bytes")
        return line

    def close(self) -> None:
        self._connection.close()
