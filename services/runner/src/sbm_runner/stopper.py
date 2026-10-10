"""Stops the bots of a match from the heartbeat thread once the runner lost its job (E152).

An admin cancels a running match by cancelling its job; the next heartbeat notices it. The bots
are killed, so the referee ends the game soon; its result is not stored.
"""

import logging
import threading

from sbm.referee import Player

log = logging.getLogger(__name__)


class Stopper:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._players: list[Player] = []
        self._stopped = False

    @property
    def stopped(self) -> bool:
        with self._lock:
            return self._stopped

    def add(self, player: Player) -> None:
        """A player added after stop is stopped at once."""
        with self._lock:
            self._players.append(player)
            if self._stopped:
                _stop(player)

    def stop(self) -> None:
        with self._lock:
            if self._stopped:
                return
            self._stopped = True
            for player in self._players:
                _stop(player)


def _stop(player: Player) -> None:
    """Players without stop end with the game; the result is discarded all the same."""
    stop = getattr(player, "stop", None)
    if stop is None:
        return
    try:
        stop()
    except Exception:
        log.exception("cannot stop %s", player.name)
