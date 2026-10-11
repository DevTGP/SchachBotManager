"""One live connection of a runner: open a match, then its moves until end (live-v1, E142)."""

import asyncio
import logging

from sbm_gateway import live_messages
from sbm_gateway.config import GatewayConfig
from sbm_gateway.feeds import Busy, FeedError, Feeds

log = logging.getLogger(__name__)

# A move with search information is far shorter; open and end are shorter still.
LINE_LIMIT = 64 * 1024


async def handle_live(
    feeds: Feeds,
    config: GatewayConfig,
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> None:
    """The gateway sends nothing back; a refused runner sees its connection close."""
    try:
        first = await asyncio.wait_for(reader.readline(), config.hello_seconds)
        match_id = live_messages.parse_open(first)
        feed = feeds.open(match_id)
    except (TimeoutError, ValueError) as error:
        # ValueError also covers InvalidMessage and a first line beyond LINE_LIMIT.
        log.warning("live connection refused: expected open: %s", error)
        writer.close()
        return
    except Busy:
        log.warning("live connection refused: the gateway follows %d matches", feeds.count)
        writer.close()
        return
    log.info("live feed of match %s opened", match_id)
    try:
        while line := await reader.readline():
            kind, move = live_messages.parse_line(line)
            if kind == "end":
                break
            feed.add(move)
    except (ValueError, FeedError) as error:
        log.warning("live feed of match %s broke the protocol: %s", match_id, error)
    except ConnectionError:
        pass
    finally:
        feeds.close(feed)
        writer.close()
    log.info("live feed of match %s closed after %d moves", match_id, feed.ply)
