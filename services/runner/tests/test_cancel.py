"""An admin cancels a running match: the runner stops the bots and stores nothing (E152)."""

import sys
import threading
import time
from dataclasses import replace
from datetime import timedelta

from bson import ObjectId
from sbm.referee import Player
from sbm_store import jobs, matches

from sbm_runner.heartbeat import Heartbeat
from sbm_runner.players import PlainPlayer
from sbm_runner.stopper import Stopper
from sbm_runner.worker import Worker, utc_now

# A bot that never says it is ready; only the cancellation ends its game early.
SILENT = [sys.executable, "-c", "import time; time.sleep(60)"]
BEAT = timedelta(milliseconds=20)


class Recording(Player):
    def __init__(self, name: str, fail: bool = False) -> None:
        super().__init__(name)
        self.stops = 0
        self._fail = fail

    def send(self, message: dict) -> None:
        pass

    def receive(self, deadline_ns: int | None) -> bytes:
        return b""

    def stop(self) -> None:
        self.stops += 1
        if self._fail:
            raise OSError("cgroup is stuck")


def wait_until(condition, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.01)
    return False


def test_stopper_stops_every_player_once_and_late_ones_at_once():
    stopper = Stopper()
    early, failing, late = Recording("early"), Recording("failing", fail=True), Recording("late")
    stopper.add(early)
    stopper.add(failing)

    stopper.stop()
    stopper.stop()
    stopper.add(late)

    assert stopper.stopped
    assert (early.stops, failing.stops, late.stops) == (1, 1, 1)


def test_heartbeat_reports_the_lost_job(db):
    jobs.insert(db, jobs.new_match_job(ObjectId(), priority=100, now=utc_now()))
    job = jobs.claim(db, jobs.MATCH, "w1", now=utc_now(), lease=timedelta(seconds=60))
    lost = threading.Event()

    with Heartbeat(
        db,
        job["_id"],
        "w1",
        lease=timedelta(seconds=60),
        interval=BEAT,
        now=utc_now,
        on_lost=lost.set,
    ):
        jobs.cancel_match(db, job["payload"]["match_id"], utc_now())
        assert lost.wait(5)


def test_a_cancelled_match_ends_early_without_a_result(db, config, reference_bots, enqueue):
    worker = Worker(
        db,
        replace(config, heartbeat=BEAT),
        players=lambda bot: PlainPlayer(bot["name"], SILENT, log=None),
        sleep=lambda _seconds: None,
    )
    match_id = enqueue(*reference_bots)

    def cancel() -> None:
        assert wait_until(lambda: matches.get(db, match_id)["status"] == matches.RUNNING)
        jobs.cancel_match(db, match_id, utc_now())
        matches.abort(db, match_id, "cancelled by an admin", utc_now())

    canceller = threading.Thread(target=cancel)
    canceller.start()
    started = time.monotonic()
    assert worker.step()
    canceller.join()

    # The silent bots would hold the game until their startup time runs out.
    assert time.monotonic() - started < 5
    match = matches.get(db, match_id)
    assert (match["status"], match["result"], match["termination"]) == (
        matches.ABORTED,
        "*",
        "aborted",
    )
    assert db.jobs.find_one({"payload.match_id": match_id})["status"] == jobs.CANCELLED
