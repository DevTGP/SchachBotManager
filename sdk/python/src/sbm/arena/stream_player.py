"""A player whose lines run over a pair of byte streams: a pipe or a TCP connection."""

import json
from typing import BinaryIO

from sbm.arena.line_reader import LineReader
from sbm.referee import Player, PlayerClosed


def encode(message: dict) -> bytes:
    return json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode() + b"\n"


class StreamPlayer(Player):
    """Subclasses connect the streams with _attach and remove them in close."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._writer: BinaryIO | None = None
        self._reader: LineReader | None = None
        # After game_over the bot may end on its own within a short grace period.
        self.finished = False

    def _attach(self, reader: BinaryIO, writer: BinaryIO) -> None:
        self._reader = LineReader(reader, self.name)
        self._writer = writer

    def send(self, message: dict) -> None:
        try:
            self._writer.write(encode(message))
            self._writer.flush()
        except (OSError, ValueError) as error:
            raise PlayerClosed(f"cannot write to the bot: {error}") from None
        if message["type"] == "game_over":
            self.finished = True

    def receive(self, deadline_ns: int | None) -> bytes:
        try:
            return self._reader.receive(deadline_ns)
        except PlayerClosed:
            raise self._closed() from None

    def _closed(self) -> PlayerClosed:
        """Why the bot's output ended, as precisely as the subclass knows."""
        return PlayerClosed("the bot closed its output")
