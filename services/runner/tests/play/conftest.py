"""The real gateway in a thread, a remote bot speaking protocol v1 over its WebSocket, and a
play worker that reaches the gateway on its local relay port.
"""

import asyncio
import json
import threading
import time
from dataclasses import replace
from datetime import timedelta

import pytest

pytest.importorskip("sbm_gateway")

from sbm import Board  # noqa: E402
from sbm.referee import STANDARD_FEN  # noqa: E402
from sbm_gateway.config import SOCKET_PATH, GatewayConfig  # noqa: E402
from sbm_gateway.server import Gateway  # noqa: E402
from sbm_store import matches, play  # noqa: E402
from sbm_store.discipline import Discipline  # noqa: E402
from websockets.exceptions import ConnectionClosed  # noqa: E402
from websockets.sync.client import connect  # noqa: E402

from sbm_runner.play.config import PlayConfig  # noqa: E402
from sbm_runner.play.worker import PlayWorker, utc_now  # noqa: E402

QUICK = Discipline("Quick", initial_time_ms=10_000, increment_ms=0, max_moves=3)
TIMEOUT = 10


class RunningGateway:
    def __init__(self) -> None:
        config = replace(GatewayConfig(), socket_host="127.0.0.1", socket_port=0, relay_port=0)
        self.gateway = Gateway(config)
        self.loop = asyncio.new_event_loop()
        started = threading.Event()

        def run() -> None:
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.gateway.start())
            started.set()
            self.loop.run_forever()

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()
        assert started.wait(TIMEOUT)

    @property
    def url(self) -> str:
        return f"ws://127.0.0.1:{self.gateway.socket_port}{SOCKET_PATH}"

    def stop(self) -> None:
        asyncio.run_coroutine_threadsafe(self.gateway.stop(), self.loop).result(TIMEOUT)
        self.loop.call_soon_threadsafe(self.loop.stop)
        self._thread.join(TIMEOUT)


class RemoteBot(threading.Thread):
    """Joins a seat and plays the first legal move each turn after delay seconds; leave_after
    ends the connection after that many own moves.
    """

    def __init__(
        self,
        url: str,
        match_id,
        seat: str,
        *,
        leave_after: int | None = None,
        delay: float = 0.0,
    ) -> None:
        super().__init__(daemon=True)
        self._url = url
        self._join = {"type": "join", "v": 1, "match_id": str(match_id), "seat": seat}
        self._leave_after = leave_after
        self._delay = delay
        self.received: list[dict] = []
        self.moves = 0

    def run(self) -> None:
        with connect(self._url, open_timeout=TIMEOUT) as socket:
            socket.send(json.dumps(self._join))
            try:
                while True:
                    message = json.loads(socket.recv(timeout=TIMEOUT))
                    self.received.append(message)
                    if not self._answer(socket, message):
                        return
            except (ConnectionClosed, TimeoutError):
                return

    def _answer(self, socket, message: dict) -> bool:
        kind = message["type"]
        if kind == "init":
            socket.send('{"type":"ready","v":1,"sdk":"0.1.0","lang":"python"}')
        elif kind == "turn":
            time.sleep(self._delay)
            move = Board.from_fen(message["fen"]).legal_moves()[0]
            socket.send(json.dumps({"type": "move", "v": 1, "move": move.uci()}))
            self.moves += 1
            if self._leave_after is not None and self.moves >= self._leave_after:
                return False
        elif kind in ("game_over", "refused"):
            return False
        return True

    def types(self) -> list[str]:
        return [message["type"] for message in self.received]


@pytest.fixture
def gateway():
    running = RunningGateway()
    yield running
    running.stop()


@pytest.fixture
def play_config(gateway) -> PlayConfig:
    return PlayConfig(
        worker_id="test-play",
        relay_port=gateway.gateway.relay_port,
        slots=1,
        connect_wait=timedelta(seconds=5),
        absent_grace=timedelta(seconds=1),
        stop_wait=timedelta(seconds=5),
    )


@pytest.fixture
def play_worker(db, play_config) -> PlayWorker:
    return PlayWorker(db, play_config, sleep=lambda _seconds: None)


@pytest.fixture
def create_remote(db, reference_bots):
    """A remote side with white against Random; returns match id and seat."""

    def create(kind: str = play.REMOTE) -> tuple:
        seat, seat_hash = play.new_seat()
        side = play.seat_side(kind, "alice", user_id=None, seat_hash=seat_hash)
        match_id = play.create(
            db,
            kind,
            side,
            matches.side(reference_bots[0]),
            QUICK,
            start_fen=STANDARD_FEN,
            now=utc_now() - timedelta(minutes=1),
        )
        return match_id, seat

    return create
