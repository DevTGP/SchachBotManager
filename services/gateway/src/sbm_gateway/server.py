"""Runs the WebSocket endpoint for clients, the relay listener for the play runner and the
live channel: the runners publish moves, viewers follow them as server-sent events (E142)."""

import asyncio
from collections.abc import Awaitable, Callable
from functools import partial

from websockets.asyncio.server import Server, serve

from sbm_gateway.client import MAX_MESSAGE_BYTES, check_path, handle_client
from sbm_gateway.config import GatewayConfig
from sbm_gateway.feeds import Feeds
from sbm_gateway.live import LINE_LIMIT as LIVE_LINE_LIMIT
from sbm_gateway.live import handle_live
from sbm_gateway.relay import LINE_LIMIT, handle_relay
from sbm_gateway.sessions import Registry
from sbm_gateway.watch import handle_watch
from sbm_gateway.watch_request import HEAD_LIMIT

Handler = Callable[[asyncio.StreamReader, asyncio.StreamWriter], Awaitable[None]]


def _tracked(handler: Handler, connections: set[asyncio.StreamWriter]) -> Handler:
    """Keeps the open connections, so stop can close them instead of waiting for them."""

    async def run(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        connections.add(writer)
        try:
            await handler(reader, writer)
        finally:
            connections.discard(writer)

    return run


class Gateway:
    """start binds all listeners; port 0 picks a free port, the bound ones are then known."""

    def __init__(self, config: GatewayConfig) -> None:
        self.config = config
        self.registry = Registry(config)
        self.feeds = Feeds(config)
        self._socket_server: Server | None = None
        self._relay_server: asyncio.Server | None = None
        self._live_server: asyncio.Server | None = None
        self._watch_server: asyncio.Server | None = None
        # Connections of runners and viewers on the live channel.
        self._channel: set[asyncio.StreamWriter] = set()
        self.socket_port = 0
        self.relay_port = 0
        self.live_port = 0
        self.watch_port = 0

    async def start(self) -> None:
        config = self.config
        self._relay_server = await asyncio.start_server(
            partial(handle_relay, self.registry, config),
            config.relay_host,
            config.relay_port,
            limit=LINE_LIMIT,
        )
        self._live_server = await asyncio.start_server(
            _tracked(partial(handle_live, self.feeds, config), self._channel),
            config.live_host,
            config.live_port,
            limit=LIVE_LINE_LIMIT,
        )
        self._watch_server = await asyncio.start_server(
            _tracked(partial(handle_watch, self.feeds, config), self._channel),
            config.watch_host,
            config.watch_port,
            limit=HEAD_LIMIT,
        )
        self._socket_server = await serve(
            partial(handle_client, self.registry, config),
            config.socket_host,
            config.socket_port,
            process_request=check_path,
            max_size=MAX_MESSAGE_BYTES,
            ping_interval=config.ping_seconds,
            ping_timeout=config.ping_seconds,
        )
        self.relay_port = self._relay_server.sockets[0].getsockname()[1]
        self.socket_port = next(iter(self._socket_server.sockets)).getsockname()[1]
        self.live_port = self._live_server.sockets[0].getsockname()[1]
        self.watch_port = self._watch_server.sockets[0].getsockname()[1]

    async def stop(self) -> None:
        """Stops accepting, refuses waiting clients and ends every game's connections. Viewers
        lose their streams without end and connect again by themselves."""
        self._relay_server.close()
        self._live_server.close()
        self._watch_server.close()
        self.feeds.shutdown()
        for writer in list(self._channel):
            writer.close()
        await self.registry.shutdown()
        self._socket_server.close()
        await self._socket_server.wait_closed()
        await self._relay_server.wait_closed()
        await self._live_server.wait_closed()
        await self._watch_server.wait_closed()
