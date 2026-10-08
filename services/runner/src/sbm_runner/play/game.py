"""Plays one interactive match: bots in the sandbox, seats through the gateway (E113).

An interactive game cannot start over, because a person or a remote bot waits for it. Every
infrastructure error therefore aborts the match without a result instead of retrying it.
"""

import logging
from collections.abc import Callable
from datetime import datetime

from pymongo.database import Database
from sbm.referee import Match, Player
from sbm_store import jobs, matches, play

from sbm_runner.game import COLORS, bot_player, store_result
from sbm_runner.match_settings import match_settings
from sbm_runner.play.config import PlayConfig
from sbm_runner.play.relay_connection import RelayConnection
from sbm_runner.play.relay_player import RelayPlayer
from sbm_runner.players import PlayerFactory, UnsupportedBot
from sbm_runner.recorder import Recorder

log = logging.getLogger(__name__)

# Opens the relay connection of a seat: (match id, seat hash) -> unopened connection.
RelayFactory = Callable[[str, str], RelayConnection]


class SeatNotTaken(Exception):
    """A person or remote bot did not take its seat in time."""


class InteractiveGame:
    """One claimed play job. cancel may be called from another thread, e.g. on shutdown."""

    def __init__(
        self,
        db: Database,
        job: dict,
        *,
        players: PlayerFactory,
        relays: RelayFactory,
        config: PlayConfig,
        now: Callable[[], datetime],
    ) -> None:
        self._db = db
        self._job = job
        self._players = players
        self._relays = relays
        self._config = config
        self._now = now
        self._connections: list[RelayConnection] = []
        self.match_id = job["payload"]["match_id"]

    def cancel(self) -> None:
        """Closes the seats' connections; the game then ends as aborted."""
        for connection in list(self._connections):
            connection.close()

    def run(self) -> None:
        match = matches.get(self._db, self.match_id)
        if match is None:
            log.error("play job %s refers to the missing match %s", self._job["_id"], self.match_id)
            jobs.fail(self._db, self._job["_id"], self._now())
            return
        if match["status"] != matches.QUEUED:
            # A runner died while it held this game; it cannot be resumed.
            self._abort("the game was interrupted and cannot be resumed")
            return
        sides: list[Player] = []
        try:
            for color in COLORS:
                sides.append(self._side(match[color]))
            self._wait_for_seats()
            if not matches.start(self._db, self.match_id, self._now()):
                raise RuntimeError("the match changed while it was being prepared")
        except Exception as error:
            for player in sides:
                player.close()
            self.cancel()
            log.warning("match %s not started: %s", self.match_id, error)
            self._abort(_reason(error))
            return
        self._play(match, *sides)

    def _play(self, match: dict, white: Player, black: Player) -> None:
        log.info("interactive match %s: %s vs %s", self.match_id, white.name, black.name)
        try:
            recorder = Recorder(self._db, self.match_id)
            record = Match(white, black, match_settings(match), on_move=recorder.on_move).play()
        except Exception as error:
            log.warning("interactive match %s aborted: %s", self.match_id, error)
            self._abort(_reason(error))
            return
        store_result(self._db, self.match_id, record, self._now())
        jobs.complete(self._db, self._job["_id"], self._job["worker_id"], self._now())
        outcome = record.outcome
        log.info("match %s: %s (%s)", self.match_id, outcome.result, outcome.termination)

    def _side(self, side: dict) -> Player:
        if side["kind"] == "bot":
            return bot_player(self._db, side, self._players)
        if side["kind"] != play.REMOTE:
            raise UnsupportedBot(f"sides of kind {side['kind']} cannot play yet")
        connection = self._relays(str(self.match_id), side["seat_hash"])
        self._connections.append(connection)
        connection.open(self._config.relay_timeout.total_seconds())
        grace = self._config.absent_grace.total_seconds()
        return RelayPlayer(side["name"], connection, absent_grace=grace)

    def _wait_for_seats(self) -> None:
        for connection in self._connections:
            if not connection.wait_present(self._config.connect_wait.total_seconds()):
                raise SeatNotTaken("the player did not connect in time")

    def _abort(self, detail: str) -> None:
        matches.abort(self._db, self.match_id, detail, self._now())
        jobs.fail(self._db, self._job["_id"], self._now())


def _reason(error: Exception) -> str:
    return f"{type(error).__name__}: {error}"
