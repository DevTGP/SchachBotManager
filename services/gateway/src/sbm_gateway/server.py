"""Runs the WebSocket endpoint for clients and the relay listener for the play runner."""

import asyncio
from functools import partial

from websockets.asyncio.server import Server, serve

from sbm_gateway.client import MAX_MESSAGE_BYTES, check_path, handle_client
from sbm_gateway.config import GatewayConfig
from sbm_gateway.relay import LINE_LIMIT, handle_relay
from sbm_gateway.sessions import Registry


class Gateway:
    """start binds both listeners; port 0 picks a free port, the bound ones are then known."""

    def __init__(self, config: GatewayConfig) -> None:
        self.config = config
        self.registry = Registry(config)
        self._socket_server: Server | None = None
        self._relay_server: asyncio.Server | None = None
        self.socket_port = 0
        self.relay_port = 0

    async def start(self) -> None:
        config = self.config
        self._relay_server = await asyncio.start_server(
            partial(handle_relay, self.registry, config),
            config.relay_host,
            config.relay_port,
            limit=LINE_LIMIT,
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

    async def stop(self) -> None:
        """Stops accepting, refuses waiting clients and ends every game's connections."""
        self._relay_server.close()
        await self.registry.shutdown()
        self._socket_server.close()
        await self._socket_server.wait_closed()
        await self._relay_server.wait_closed()
