"""One WebSocket connection: join a seat, then carry the game protocol (gateway-v1)."""

import asyncio
import logging
from http import HTTPStatus

from websockets.asyncio.server import ServerConnection
from websockets.exceptions import ConnectionClosed
from websockets.http11 import Request, Response

from sbm_gateway import messages
from sbm_gateway.config import SOCKET_PATH, GatewayConfig
from sbm_gateway.links import SocketClient
from sbm_gateway.sessions import REPLACED, SHUTDOWN, Registry, Session

log = logging.getLogger(__name__)

# A line may hold 65536 characters of up to four bytes each in UTF-8.
MAX_MESSAGE_BYTES = 4 * messages.MAX_LINE_CHARS + 1024
CLOSE_UNSUPPORTED = 1003
CLOSE_TOO_BIG = 1009


def check_path(connection: ServerConnection, request: Request) -> Response | None:
    """Only the socket path upgrades; nginx forwards nothing else, but the check is cheap."""
    if request.path != SOCKET_PATH:
        return connection.respond(HTTPStatus.NOT_FOUND, "not found\n")
    return None


async def handle_client(registry: Registry, config: GatewayConfig, socket: ServerConnection):
    client = SocketClient(socket)
    if registry.clients >= config.max_clients:
        await client.refuse("busy", "too many connections", wait=True)
        return
    registry.clients += 1
    try:
        session = await _join(registry, config, client)
        if session is not None:
            await _carry(session, client)
    finally:
        registry.clients -= 1


async def _join(registry: Registry, config: GatewayConfig, client: SocketClient) -> Session | None:
    try:
        first = await asyncio.wait_for(client.socket.recv(), config.hello_seconds)
        match_id, seat = messages.parse_join(first)
    except (TimeoutError, messages.InvalidMessage) as error:
        await client.refuse(
            "invalid_message", f"the first message must be join: {error}", wait=True
        )
        return None
    except ConnectionClosed:
        return None
    result = await registry.join((match_id, messages.seat_hash(seat)), client)
    if result is None:
        await client.refuse("no_game", "no game is waiting for this seat", wait=True)
    elif result is REPLACED:
        await client.refuse("replaced", "a newer connection took this seat", wait=True)
    elif result is SHUTDOWN:
        await client.refuse("shutdown", "the gateway stops", wait=True)
    else:
        log.info("client joined match %s", match_id)
        return result
    return None


async def _carry(session: Session, client: SocketClient) -> None:
    socket = client.socket
    try:
        async for message in socket:
            if not isinstance(message, str):
                await socket.close(CLOSE_UNSUPPORTED, "text messages only")
                break
            if len(message) > messages.MAX_LINE_CHARS:
                await socket.close(CLOSE_TOO_BIG, "a message holds at most 65536 characters")
                break
            await session.to_runner(client, message)
    except ConnectionClosed:
        pass
    finally:
        await session.leave(client)
