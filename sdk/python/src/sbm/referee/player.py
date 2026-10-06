"""The interface between the referee and one side of a game (match-runner.md, Spieler-Adapter).

An adapter starts and stops the side and carries protocol lines; the referee decides about
everything else. Deadlines are values of time.monotonic_ns(), None means no deadline.
"""

from abc import ABC, abstractmethod

MAX_LINE_BYTES = 65_536


class PlayerTimeout(Exception):
    """No line arrived before the deadline."""


class PlayerClosed(Exception):
    """The side is gone: the process ended or the connection closed.

    termination is the code the referee scores, crash unless the adapter knows better, e.g.
    memory_limit when the sandbox stopped the process.
    """

    def __init__(self, message: str, termination: str = "crash") -> None:
        super().__init__(message)
        self.termination = termination


class LineTooLong(Exception):
    """The side wrote a line longer than MAX_LINE_BYTES."""


class Player(ABC):
    """One side of a game. Other exceptions than the ones above are infrastructure errors."""

    def __init__(self, name: str) -> None:
        self.name = name

    def start(self) -> None:  # noqa: B027
        """Starts the side, e.g. launches its process; part of the startup budget."""

    @abstractmethod
    def send(self, message: dict) -> None:
        """Writes one message as one line; raises PlayerClosed."""

    @abstractmethod
    def receive(self, deadline_ns: int | None) -> bytes:
        """The next line without its line end.

        A line that is already waiting is returned even if the deadline has passed. Raises
        PlayerTimeout, PlayerClosed or LineTooLong.
        """

    def suspend(self) -> None:  # noqa: B027
        """Called after each own turn; the server freezes the process here."""

    def resume(self) -> None:  # noqa: B027
        """Called before each own turn and before game_over."""

    def close(self) -> None:  # noqa: B027
        """Ends the side after game_over, with a short grace period to exit on its own."""
