"""A gateway that plays the referee's part of a short game, for remote tests (E116, E120)."""

import asyncio
import contextlib
import json
import threading

from protocol_schemas import example
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed

TOKEN = "sbm_" + "A" * 43
SEAT = "Xq3v7dK2mP9sL1wR8tY4uB6nC0eF5gH2jA7kZ3xQ_-M"
MATCH_ID = "6523a1f0c2d4e5f6a7b8c9d0"


class FakeGateway:
    """Accepts one join, then plays the referee's part of a game from MESSAGES."""

    def __init__(self, messages: list[dict], *, ping: float | None = None) -> None:
        self.messages = messages
        self.received: list = []
        self.pongs_missed = False
        self.loop = asyncio.new_event_loop()
        self.ping = ping
        started = threading.Event()

        def run():
            asyncio.set_event_loop(self.loop)

            async def start():
                return await serve(
                    self.handle, "127.0.0.1", 0, ping_interval=ping, ping_timeout=ping
                )

            self.server = self.loop.run_until_complete(start())
            self.port = next(iter(self.server.sockets)).getsockname()[1]
            started.set()
            self.loop.run_forever()

        threading.Thread(target=run, daemon=True).start()
        assert started.wait(5)

    @property
    def url(self) -> str:
        return f"ws://127.0.0.1:{self.port}/api/v1/play/socket"

    async def handle(self, socket):
        with contextlib.suppress(ConnectionClosed):
            await self._play(socket)

    async def _play(self, socket):
        join = json.loads(await socket.recv())
        self.received.append(join)
        if join.get("seat") != SEAT:
            await socket.send(
                json.dumps({"type": "refused", "v": 1, "code": "no_game", "message": "?"})
            )
            return
        await socket.send(json.dumps({"type": "joined", "v": 1, "match_id": MATCH_ID}))
        for message in self.messages:
            await socket.send(json.dumps(message))
            if message["type"] in ("init", "turn"):
                self.received.append(json.loads(await socket.recv()))
        await socket.close()

    def stop(self):
        async def shutdown():
            self.server.close()
            await self.server.wait_closed()

        asyncio.run_coroutine_threadsafe(shutdown(), self.loop).result(5)
        self.loop.call_soon_threadsafe(self.loop.stop)


GAME = [example("init.standard"), example("turn.first_move"), example("game_over.checkmate")]
