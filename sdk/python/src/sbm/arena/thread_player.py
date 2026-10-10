"""A bot class that plays in a thread of the calling program, for play (E120).

The bot speaks the protocol over a local socket pair, so the referee treats it like any other
player and a debugger stops at its breakpoints. A thread cannot be frozen: suspend and resume
do nothing, as for a TCP bot.
"""

import contextlib
import socket
import threading

from sbm.arena.stream_player import StreamPlayer
from sbm.bot import Bot
from sbm.channel import Channel, ProtocolError
from sbm.game import BotError, Game, guarded

# Time the thread gets to end after game_over; a bot still thinking after a timeout keeps
# running until choose_move returns, and its answer goes nowhere.
JOIN_SECONDS = 2.0


class ThreadPlayer(StreamPlayer):
    """error holds what ended the bot's side early: a BotError or a ProtocolError."""

    def __init__(self, name: str, bot: type[Bot]) -> None:
        super().__init__(name)
        self._bot = bot
        self._socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self.error: BotError | ProtocolError | None = None

    def start(self) -> None:
        own, other = socket.socketpair()
        self._socket = own
        self._attach(own.makefile("rb"), own.makefile("wb"))
        self._thread = threading.Thread(
            target=self._play, args=(other,), name=f"bot {self.name}", daemon=True
        )
        self._thread.start()

    def _play(self, connection: socket.socket) -> None:
        with Channel(connection.makefile("rb"), connection.makefile("wb"), connection) as channel:
            try:
                Game(guarded(f"{self._bot.__name__}()", self._bot), channel).play()
            except (BotError, ProtocolError) as error:
                self.error = error
            except (OSError, ValueError):
                pass  # the referee closed the connection, e.g. after a timeout

    def close(self) -> None:
        if self._socket is None:
            return
        with contextlib.suppress(OSError, ValueError):
            self._writer.close()
        with contextlib.suppress(OSError):
            self._socket.shutdown(socket.SHUT_RDWR)
        self._socket.close()
        self._thread.join(JOIN_SECONDS)
