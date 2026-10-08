"""The play runner's main loop: up to slots interactive games at once, each in its own thread."""

import logging
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime

from pymongo.database import Database
from pymongo.errors import PyMongoError
from sbm_store import jobs, matches, play

from sbm_runner.heartbeat import Heartbeat
from sbm_runner.play.config import PlayConfig
from sbm_runner.play.game import InteractiveGame, RelayFactory
from sbm_runner.play.relay_connection import RelayConnection
from sbm_runner.players import PlayerFactory, plain_player
from sbm_runner.shutdown import Shutdown

log = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(UTC)


class PlayWorker:
    def __init__(
        self,
        db: Database,
        config: PlayConfig,
        *,
        players: PlayerFactory = plain_player,
        relays: RelayFactory | None = None,
        now: Callable[[], datetime] = utc_now,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._db = db
        self._config = config
        self._players = players
        self._relays = relays or (
            lambda match_id, seat_hash: RelayConnection(config.relay_address, match_id, seat_hash)
        )
        self._now = now
        self._sleep = sleep
        self._games: dict[threading.Thread, InteractiveGame] = {}

    @property
    def running(self) -> int:
        return len(self._games)

    def run(self, should_stop: Callable[[], bool] = lambda: False) -> None:
        """Runs until should_stop says so or Shutdown is raised; then aborts running games."""
        try:
            while not should_stop():
                try:
                    worked = self.step()
                except PyMongoError as error:
                    log.warning("database unavailable: %s", error)
                    worked = False
                if not worked:
                    self._sleep(self._config.poll_interval.total_seconds())
        except Shutdown:
            self.stop()
            raise
        self.stop()

    def step(self) -> bool:
        """Starts one game if a slot is free; False if nothing was started."""
        self._reap()
        recover_expired_play(self._db, self._now())
        if self.running >= self._config.slots:
            return False
        job = jobs.claim(
            self._db,
            play.PLAY_JOB,
            self._config.worker_id,
            now=self._now(),
            lease=self._config.lease,
        )
        if job is None:
            return False
        game = InteractiveGame(
            self._db,
            job,
            players=self._players,
            relays=self._relays,
            config=self._config,
            now=self._now,
        )
        thread = threading.Thread(
            target=self._run_game, args=(job, game), name=f"play {game.match_id}", daemon=True
        )
        self._games[thread] = game
        thread.start()
        return True

    def stop(self) -> None:
        """Ends every running game: its seats close, so it ends as aborted."""
        for game in list(self._games.values()):
            game.cancel()
        deadline = time.monotonic() + self._config.stop_wait.total_seconds()
        for thread in list(self._games):
            thread.join(max(0.0, deadline - time.monotonic()))
        for thread, game in list(self._games.items()):
            if thread.is_alive():
                # Its bot did not finish its turn in time; the container stops it.
                matches.abort(self._db, game.match_id, "the play runner stopped", self._now())
        self._reap()

    def _run_game(self, job: dict, game: InteractiveGame) -> None:
        heartbeat = Heartbeat(
            self._db,
            job["_id"],
            self._config.worker_id,
            lease=self._config.lease,
            interval=self._config.heartbeat,
            now=self._now,
        )
        try:
            with heartbeat:
                game.run()
        except Exception:
            log.exception("interactive match %s failed", game.match_id)
            matches.abort(self._db, game.match_id, "internal error of the play runner", self._now())
            jobs.fail(self._db, job["_id"], self._now())

    def _reap(self) -> None:
        for thread in [thread for thread in self._games if not thread.is_alive()]:
            del self._games[thread]


def recover_expired_play(db: Database, now: datetime) -> int:
    """Gives up play jobs whose runner died: an interactive game cannot start over."""
    handled = 0
    for job in jobs.expired(db, play.PLAY_JOB, now):
        if jobs.fail_expired(db, job, now):
            matches.abort(db, job["payload"]["match_id"], "the play runner stopped responding", now)
            log.error("play job %s lost its runner %s, match aborted", job["_id"], job["worker_id"])
            handled += 1
    return handled
