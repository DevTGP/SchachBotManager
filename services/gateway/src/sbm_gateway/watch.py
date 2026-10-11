"""One viewer: the moves of a running match as server-sent events (E102, E142).

The stream starts with the moves after the ply the viewer names, follows the match move by
move and ends with the event end. A match no runner publishes within a few seconds is answered
with 404; the viewer then asks the API instead.
"""

import asyncio
import json
from http import HTTPStatus

from sbm_gateway import events
from sbm_gateway.config import GatewayConfig
from sbm_gateway.feeds import CLOSE, Feed, Feeds
from sbm_gateway.watch_request import BadRequest, parse_head

# X-Accel-Buffering keeps nginx and the proxy in front of it from holding events back.
_STREAM_HEAD = (
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: text/event-stream; charset=utf-8\r\n"
    "Cache-Control: no-store\r\n"
    "X-Accel-Buffering: no\r\n"
    "Connection: close\r\n"
    "\r\n"
)


async def handle_watch(
    feeds: Feeds,
    config: GatewayConfig,
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> None:
    try:
        try:
            head = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), config.hello_seconds)
            request = parse_head(head)
        except BadRequest as error:
            await _refuse(writer, error.status, error.code, str(error))
            return
        except (TimeoutError, asyncio.IncompleteReadError, asyncio.LimitOverrunError):
            await _refuse(writer, HTTPStatus.BAD_REQUEST, "invalid_request", "incomplete request")
            return
        if feeds.watchers >= config.max_watchers:
            await _refuse(writer, HTTPStatus.SERVICE_UNAVAILABLE, "busy", "too many viewers")
            return
        feeds.watchers += 1
        try:
            feed = await feeds.find(request.match_id, config.feed_wait_seconds)
            if feed is None:
                await _refuse(writer, HTTPStatus.NOT_FOUND, "not_live", "the match is not live")
            else:
                await _stream(feed, request.after, config, writer)
        finally:
            feeds.watchers -= 1
    except ConnectionError:
        pass
    finally:
        writer.close()


async def _stream(
    feed: Feed, after: int, config: GatewayConfig, writer: asyncio.StreamWriter
) -> None:
    writer.write((_STREAM_HEAD + events.RETRY).encode())
    await writer.drain()
    watcher = feed.watch(after)
    try:
        while True:
            try:
                event = await asyncio.wait_for(watcher.get(), config.watch_ping_seconds)
            except TimeoutError:
                event = events.PING
            if event is CLOSE:
                return
            writer.write(event.encode())
            await writer.drain()
            if event == events.END:
                return
    finally:
        feed.unwatch(watcher)


async def _refuse(writer: asyncio.StreamWriter, status: HTTPStatus, code: str, text: str) -> None:
    """The error body of the web API (code and message)."""
    body = json.dumps({"code": code, "message": text}).encode()
    head = (
        f"HTTP/1.1 {status.value} {status.phrase}\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Cache-Control: no-store\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    writer.write(head.encode() + body)
    await writer.drain()
