"""A gateway on free local ports, run in a thread of its own; helpers for both ends."""

import asyncio
import json
import socket
import threading
from dataclasses import replace

import pytest
from websockets.sync.client import ClientConnection, connect

from sbm_gateway.config import SOCKET_PATH, GatewayConfig
from sbm_gateway.messages import seat_hash
from sbm_gateway.server import Gateway

MATCH_ID = "6523a1f0c2d4e5f6a7b8c9d0"
SEAT = "Xq3v7dK2mP9sL1wR8tY4uB6nC0eF5gH2jA7kZ3xQ_-M"
TIMEOUT = 5


class RunningGateway:
    def __init__(self, config: GatewayConfig) -> None:
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

    def client(self) -> ClientConnection:
        url = f"ws://127.0.0.1:{self.gateway.socket_port}{SOCKET_PATH}"
        return connect(url, open_timeout=TIMEOUT)

    def relay(self) -> "RelayEnd":
        return RelayEnd(socket.create_connection(("127.0.0.1", self.gateway.relay_port), TIMEOUT))

    def stop(self) -> None:
        asyncio.run_coroutine_threadsafe(self.gateway.stop(), self.loop).result(TIMEOUT)
        self.loop.call_soon_threadsafe(self.loop.stop)
        self._thread.join(TIMEOUT)


class RelayEnd:
    """The runner's side of a relay connection."""

    def __init__(self, connection: socket.socket) -> None:
        self.connection = connection
        self.reader = connection.makefile("rb")

    def send(self, message: dict) -> None:
        self.connection.sendall(json.dumps(message).encode() + b"\n")

    def attach(self, match_id: str = MATCH_ID, seat: str = SEAT) -> None:
        self.send({"type": "attach", "v": 1, "match_id": match_id, "seat_hash": seat_hash(seat)})

    def line(self, data: str) -> None:
        self.send({"type": "line", "data": data})

    def receive(self) -> dict | None:
        line = self.reader.readline()
        return json.loads(line) if line else None

    def close(self) -> None:
        self.reader.close()
        self.connection.close()


def join(client: ClientConnection, match_id: str = MATCH_ID, seat: str = SEAT) -> None:
    client.send(json.dumps({"type": "join", "v": 1, "match_id": match_id, "seat": seat}))


def receive(client: ClientConnection) -> dict:
    return json.loads(client.recv(timeout=TIMEOUT))


@pytest.fixture
def config() -> GatewayConfig:
    return replace(
        GatewayConfig(), socket_host="127.0.0.1", socket_port=0, relay_port=0, join_wait_seconds=2
    )


@pytest.fixture
def gateway(config: GatewayConfig):
    running = RunningGateway(config)
    yield running
    running.stop()
