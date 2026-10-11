"""Plays one interactive match: bots in the sandbox, seats through the gateway (E113).

An interactive game cannot start over, because a person or a remote bot waits for it. Every
infrastructure error therefore aborts the match without a result instead of retrying it.

A league or tournament game with an account is different (E185): it starts after connect_wait
even without its people, whose clocks run while they are away, and an infrastructure error puts
it back to wait for readiness again instead of aborting it.
"""

import logging
import math
import time
from collections.abc import Callable
from datetime import datetime

from bson import ObjectId
from pymongo.database import Database
from sbm.referee import Match, MatchRecord, MoveRecord, Player
from sbm_store import competition_readiness, jobs, matches, play

from sbm_runner.game import COLORS, bot_player
from sbm_runner.live_feed import LiveFeed
from sbm_runner.match_settings import match_settings
from sbm_runner.play.config import PlayConfig
from sbm_runner.play.human_player import HumanPlayer
from sbm_runner.play.relay_connection import RelayConnection
from sbm_runner.play.relay_player import RelayPlayer
from sbm_runner.players import PlayerFactory, UnsupportedBot
from sbm_runner.recorder import Recorder, move_document

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
        self._people: list[HumanPlayer] = []
        self.match_id = job["payload"]["match_id"]
        # Known from the job, so a stop before the match is read resets it as well.
        self.competition = bool(job["payload"].get("competition"))

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
        self.competition = competition_readiness.is_competition(match)
        if match["status"] != matches.QUEUED:
            # A runner died while it held this game; it cannot be resumed.
            self._abort("the game was interrupted and cannot be resumed")
            return
        sides: list[Player] = []
        try:
            for color in COLORS:
                sides.append(self._side(match[color]))
            self._wait_for_seats()
        except Exception as error:
            self._refuse(sides, error)
            return
        # Opened before the start, so a viewer that sees the match running finds its feed (E142).
        feed = LiveFeed(self._config.live_address, self.match_id)
        feed.open()
        try:
            if not matches.start(self._db, self.match_id, self._now()):
                self._refuse(sides, RuntimeError("the match changed while it was being prepared"))
                return
            self._play(match, *sides, feed=feed)
        finally:
            # After the result or the abort, so a viewer told end finds it in the API.
            feed.end()

    def _refuse(self, sides: list[Player], error: Exception) -> None:
        for player in sides:
            player.close()
        self.cancel()
        log.warning("match %s not started: %s", self.match_id, error)
        self._abort(_reason(error))

    def _play(self, match: dict, white: Player, black: Player, *, feed: LiveFeed) -> None:
        log.info("interactive match %s: %s vs %s", self.match_id, white.name, black.name)
        try:
            recorder = Recorder(self._db, self.match_id)

            def on_move(move: MoveRecord) -> None:
                recorder.on_move(move)
                feed.move(move_document(move))
                for person in self._people:
                    person.observe(move)

            record = Match(white, black, match_settings(match), on_move=on_move).play()
        except Exception as error:
            log.warning("interactive match %s aborted: %s", self.match_id, error)
            self._abort(_reason(error))
            return
        self._store(match, record)
        jobs.complete(self._db, self._job["_id"], self._job["worker_id"], self._now())
        outcome = record.outcome
        log.info("match %s: %s (%s)", self.match_id, outcome.result, outcome.termination)

    def _side(self, side: dict) -> Player:
        if side["kind"] == "bot":
            return bot_player(self._db, side, self._players)
        if side["kind"] not in play.SEAT_KINDS:
            raise UnsupportedBot(f"sides of kind {side['kind']} cannot play")
        connection = self._relays(str(self.match_id), side["seat_hash"])
        self._connections.append(connection)
        connection.open(self._config.relay_timeout.total_seconds())
        # In a competition game the clock of an absent person runs out instead (E185).
        grace = math.inf if self.competition else self._config.absent_grace.total_seconds()
        if side["kind"] == play.REMOTE:
            return RelayPlayer(side["name"], connection, absent_grace=grace)
        person = HumanPlayer(side["name"], connection, absent_grace=grace)
        self._people.append(person)
        return person

    def _store(self, match: dict, record: MatchRecord) -> None:
        """A person has no SDK; bots and remote bots keep what their ready said."""
        outcome = record.outcome
        sides = {}
        for color, side in zip(COLORS, (record.white, record.black), strict=True):
            person = match[color]["kind"] == play.HUMAN
            sides[color] = {
                "sdk": None if person else side.sdk,
                "lang": None if person else side.lang,
            }
        matches.finish(
            self._db,
            self.match_id,
            sides=sides,
            result=outcome.result,
            termination=outcome.termination,
            detail=outcome.detail,
            now=self._now(),
        )

    def _wait_for_seats(self) -> None:
        """Up to connect_wait in all; a competition game then starts without the absent."""
        deadline = time.monotonic() + self._config.connect_wait.total_seconds()
        for connection in self._connections:
            if not connection.wait_present(max(0.0, deadline - time.monotonic())):
                if self.competition:
                    log.info("match %s starts without a player who is away", self.match_id)
                    continue
                raise SeatNotTaken("the player did not connect in time")

    def _abort(self, detail: str) -> None:
        give_up(self._db, self.match_id, detail, self._now(), competition=self.competition)
        jobs.fail(self._db, self._job["_id"], self._now())


def give_up(
    db: Database, match_id: ObjectId, detail: str, now: datetime, *, competition: bool
) -> None:
    """Aborts an interactive game; a competition game waits for readiness again (E185)."""
    if competition and competition_readiness.reset(db, match_id, now):
        log.warning("competition match %s reset: %s", match_id, detail)
        return
    matches.abort(db, match_id, detail, now)


def _reason(error: Exception) -> str:
    return f"{type(error).__name__}: {error}"
