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

    def live(self) -> "LiveEnd":
        return LiveEnd(socket.create_connection(("127.0.0.1", self.gateway.live_port), TIMEOUT))

    def watch(self, target: str, method: str = "GET", headers: str = "") -> "WatchEnd":
        connection = socket.create_connection(("127.0.0.1", self.gateway.watch_port), TIMEOUT)
        request = f"{method} {target} HTTP/1.1\r\nHost: sbm\r\n{headers}\r\n"
        connection.sendall(request.encode("latin-1"))
        return WatchEnd(connection)

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


class LiveEnd:
    """The runner's side of a live connection."""

    def __init__(self, connection: socket.socket) -> None:
        self.connection = connection

    def send(self, message: dict) -> None:
        self.connection.sendall(json.dumps(message).encode() + b"\n")

    def open(self, match_id: str = MATCH_ID) -> None:
        self.send({"type": "open", "v": 1, "match_id": match_id})

    def move(self, ply: int) -> None:
        self.send({"type": "move", "move": move(ply)})

    def end(self) -> None:
        self.send({"type": "end"})

    def closed(self) -> bool:
        """True once the gateway closed the connection."""
        return self.connection.recv(1) == b""

    def close(self) -> None:
        self.connection.close()


class WatchEnd:
    """A viewer's HTTP connection: the status, the headers, then events one by one."""

    def __init__(self, connection: socket.socket) -> None:
        self.connection = connection
        self.reader = connection.makefile("rb")
        status_line = self.reader.readline().decode("latin-1")
        self.status = int(status_line.split(" ")[1])
        self.headers: dict[str, str] = {}
        while (line := self.reader.readline().decode("latin-1").rstrip("\r\n")) != "":
            name, _, value = line.partition(":")
            self.headers[name.strip().lower()] = value.strip()

    def body(self) -> dict:
        return json.loads(self.reader.read(int(self.headers["content-length"])))

    def event(self) -> dict[str, str] | None:
        """The fields of the next event (comments and retry left out); None at the end."""
        fields: dict[str, str] = {}
        while True:
            line = self.reader.readline().decode()
            if not line:
                return None
            line = line.rstrip("\n")
            if line == "":
                if fields:
                    return fields
                continue
            name, _, value = line.partition(": ")
            if name and name != "retry":
                fields[name] = value

    def comment(self) -> str:
        return self.reader.readline().decode().rstrip("\n")

    def close(self) -> None:
        self.reader.close()
        self.connection.close()


def move(ply: int) -> dict:
    return {
        "ply": ply,
        "uci": "e2e4",
        "san": "e4",
        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
        "spent_ms": 10,
        "clock_ms": 1000,
        "info": None,
    }


def join(client: ClientConnection, match_id: str = MATCH_ID, seat: str = SEAT) -> None:
    client.send(json.dumps({"type": "join", "v": 1, "match_id": match_id, "seat": seat}))


def receive(client: ClientConnection) -> dict:
    return json.loads(client.recv(timeout=TIMEOUT))


@pytest.fixture
def config() -> GatewayConfig:
    return replace(
        GatewayConfig(),
        socket_host="127.0.0.1",
        socket_port=0,
        relay_port=0,
        live_port=0,
        watch_host="127.0.0.1",
        watch_port=0,
        join_wait_seconds=2,
        feed_wait_seconds=0.5,
    )


@pytest.fixture
def gateway(config: GatewayConfig):
    running = RunningGateway(config)
    yield running
    running.stop()
