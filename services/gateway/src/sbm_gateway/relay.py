"""One relay connection of the play runner: attach a seat, then carry lines (relay-v1)."""

import asyncio
import logging

from sbm_gateway import messages
from sbm_gateway.config import GatewayConfig
from sbm_gateway.links import RelayLink
from sbm_gateway.sessions import PendingOverflow, Refused, Registry

log = logging.getLogger(__name__)

# A line message holds up to 65536 characters, escaped in JSON up to six bytes each.
LINE_LIMIT = 6 * messages.MAX_LINE_CHARS + 1024


async def handle_relay(
    registry: Registry,
    config: GatewayConfig,
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> None:
    relay = RelayLink(writer)
    try:
        first = await asyncio.wait_for(reader.readline(), config.hello_seconds)
        key = messages.parse_attach(first)
        session = await registry.attach(key, relay)
    except (TimeoutError, ValueError, messages.InvalidMessage) as error:
        # ValueError also covers a first line beyond LINE_LIMIT.
        await relay.send(messages.refused_relay("invalid_message", f"expected attach: {error}"))
        relay.close()
        return
    except Refused as refusal:
        await relay.send(messages.refused_relay(refusal.code, str(refusal)))
        relay.close()
        return
    log.info("runner attached match %s", key[0])
    reason = "game over"
    try:
        while line := await reader.readline():
            await session.to_client(messages.parse_line(line))
    except (ValueError, messages.InvalidMessage) as error:
        log.warning("relay of match %s broke the protocol: %s", key[0], error)
        reason = "relay error"
    except PendingOverflow:
        log.warning("client of match %s missed too many lines", key[0])
        reason = "the client was away too long"
    except ConnectionError:
        reason = "relay error"
    finally:
        await registry.detach(session, reason)
        relay.close()
    log.info("runner detached match %s (%s)", key[0], reason)
