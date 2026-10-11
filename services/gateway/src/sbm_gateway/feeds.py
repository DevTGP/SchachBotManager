"""The running matches the runners publish and the viewers that follow them (E142).

A feed exists while a runner's live connection for its match is open. It keeps every move as
an event, so a viewer that comes later first gets the moves it lacks. A newer connection for
the same match replaces the feed; the viewers of the older one get end and ask the API again.
"""

import asyncio

from sbm_gateway import events
from sbm_gateway.config import GatewayConfig

# Ends a viewer's stream without the event end, e.g. on shutdown: the browser then connects
# again by itself and finds the match on the next gateway.
CLOSE = None


class FeedError(Exception):
    """A runner sent moves out of order or more than the gateway keeps."""


class Busy(Exception):
    """The gateway follows as many matches as it may."""


class Feed:
    def __init__(self, match_id: str, max_moves: int) -> None:
        self.match_id = match_id
        self._moves: list[str] = []
        self._max_moves = max_moves
        self._watchers: set[asyncio.Queue] = set()
        self.ended = False

    @property
    def ply(self) -> int:
        return len(self._moves)

    def add(self, move: dict) -> None:
        """Ignored once the feed ended, e.g. after a newer connection replaced it."""
        if self.ended:
            return
        if move["ply"] != self.ply + 1:
            raise FeedError(f"expected ply {self.ply + 1}, got {move['ply']}")
        if self.ply >= self._max_moves:
            raise FeedError(f"the gateway keeps at most {self._max_moves} moves")
        event = events.move(move)
        self._moves.append(event)
        for watcher in self._watchers:
            watcher.put_nowait(event)

    def end(self, last: str | None = events.END) -> None:
        if self.ended:
            return
        self.ended = True
        for watcher in self._watchers:
            watcher.put_nowait(last)

    def watch(self, after: int) -> asyncio.Queue:
        """A queue of the events after ply `after`, then each new one, then END or CLOSE."""
        watcher: asyncio.Queue = asyncio.Queue()
        for event in self._moves[after:]:
            watcher.put_nowait(event)
        if self.ended:
            watcher.put_nowait(events.END)
        self._watchers.add(watcher)
        return watcher

    def unwatch(self, watcher: asyncio.Queue) -> None:
        self._watchers.discard(watcher)


class Feeds:
    def __init__(self, config: GatewayConfig) -> None:
        self._config = config
        self._feeds: dict[str, Feed] = {}
        self._opened = asyncio.Event()
        self.watchers = 0

    @property
    def count(self) -> int:
        return len(self._feeds)

    def open(self, match_id: str) -> Feed:
        """Raises Busy."""
        older = self._feeds.pop(match_id, None)
        if older is not None:
            older.end()
        if len(self._feeds) >= self._config.max_feeds:
            raise Busy()
        feed = Feed(match_id, self._config.max_feed_moves)
        self._feeds[match_id] = feed
        # Wakes every viewer waiting in find; each one looks for its match again.
        self._opened.set()
        self._opened = asyncio.Event()
        return feed

    def close(self, feed: Feed) -> None:
        feed.end()
        if self._feeds.get(feed.match_id) is feed:
            del self._feeds[feed.match_id]

    async def find(self, match_id: str, wait: float) -> Feed | None:
        """The feed of the match; waits up to `wait` seconds for its runner to open it."""
        loop = asyncio.get_running_loop()
        deadline = loop.time() + wait
        while (feed := self._feeds.get(match_id)) is None:
            remaining = deadline - loop.time()
            if remaining <= 0:
                return None
            try:
                await asyncio.wait_for(self._opened.wait(), remaining)
            except TimeoutError:
                return None
        return feed

    def shutdown(self) -> None:
        """Ends every viewer's stream without end, so browsers connect again by themselves."""
        for feed in list(self._feeds.values()):
            feed.end(CLOSE)
        self._feeds.clear()
