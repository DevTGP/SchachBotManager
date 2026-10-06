"""The two bots of a series; each game gets a fresh player, as a bot plays one game per process."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TextIO

from sbm.arena.bot_spec import BotSpec
from sbm.arena.process_player import ProcessPlayer
from sbm.arena.tcp_player import TcpListener, connect
from sbm.referee import Player


class Entrant(ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def player(self) -> Player:
        """A player for the next game; may wait, e.g. for a TCP bot to connect."""

    def close(self) -> None:  # noqa: B027
        """Releases what the entrant holds for the whole series."""


class ProcessEntrant(Entrant):
    def __init__(self, name: str, command: list[str] | str, log: TextIO | None) -> None:
        super().__init__(name)
        self._command = command
        self._log = log

    def player(self) -> Player:
        return ProcessPlayer(self.name, self._command, log=self._log)


class TcpEntrant(Entrant):
    def __init__(self, name: str, port: int, announce: Callable[[str], None]) -> None:
        super().__init__(name)
        self._listener = TcpListener(port)
        self._announce = announce

    def player(self) -> Player:
        return connect(self.name, self._listener, self._announce)

    def close(self) -> None:
        self._listener.close()


def create_entrant(spec: BotSpec, log: TextIO | None, announce: Callable[[str], None]) -> Entrant:
    """Raises OSError if the TCP port cannot be opened."""
    if spec.port is not None:
        return TcpEntrant(spec.name, spec.port, announce)
    return ProcessEntrant(spec.name, spec.command, log)
