import asyncio
from dataclasses import replace

import pytest
from conftest import MATCH_ID, move

from sbm_gateway import events
from sbm_gateway.config import GatewayConfig
from sbm_gateway.feeds import CLOSE, Busy, Feed, FeedError, Feeds

OTHER_MATCH = "0" * 24


def drain(watcher: asyncio.Queue) -> list:
    items = []
    while not watcher.empty():
        items.append(watcher.get_nowait())
    return items


def test_a_late_viewer_gets_the_moves_after_its_ply_then_the_new_ones():
    feed = Feed(MATCH_ID, 10)
    for ply in (1, 2, 3):
        feed.add(move(ply))
    watcher = feed.watch(1)
    feed.add(move(4))
    feed.end()
    assert drain(watcher) == [
        events.move(move(2)),
        events.move(move(3)),
        events.move(move(4)),
        events.END,
    ]


def test_a_viewer_of_an_ended_feed_gets_end_after_the_moves():
    feed = Feed(MATCH_ID, 10)
    feed.add(move(1))
    feed.end()
    assert drain(feed.watch(0)) == [events.move(move(1)), events.END]


def test_moves_come_in_order_and_up_to_the_limit():
    feed = Feed(MATCH_ID, 2)
    with pytest.raises(FeedError):
        feed.add(move(2))
    feed.add(move(1))
    feed.add(move(2))
    with pytest.raises(FeedError):
        feed.add(move(3))


def test_an_ended_feed_ignores_moves_and_ends_once():
    feed = Feed(MATCH_ID, 10)
    watcher = feed.watch(0)
    feed.end()
    feed.end(CLOSE)
    feed.add(move(1))
    assert drain(watcher) == [events.END]
    assert feed.ply == 0


def test_a_newer_feed_replaces_the_older():
    async def scenario():
        feeds = Feeds(GatewayConfig())
        older = feeds.open(MATCH_ID)
        watcher = older.watch(0)
        newer = feeds.open(MATCH_ID)
        assert await feeds.find(MATCH_ID, 0) is newer
        assert drain(watcher) == [events.END]
        # The older connection closing later leaves the newer feed alone.
        feeds.close(older)
        assert await feeds.find(MATCH_ID, 0) is newer
        feeds.close(newer)
        assert await feeds.find(MATCH_ID, 0) is None

    asyncio.run(scenario())


def test_find_waits_for_the_runner_to_open():
    async def scenario():
        feeds = Feeds(GatewayConfig())
        search = asyncio.create_task(feeds.find(MATCH_ID, 5))
        await asyncio.sleep(0)
        feeds.open(OTHER_MATCH)
        await asyncio.sleep(0)
        assert not search.done()
        feed = feeds.open(MATCH_ID)
        assert await search is feed
        assert await feeds.find("1" * 24, 0.05) is None

    asyncio.run(scenario())


def test_the_gateway_follows_a_limited_number_of_matches():
    async def scenario():
        feeds = Feeds(replace(GatewayConfig(), max_feeds=1))
        feeds.open(MATCH_ID)
        with pytest.raises(Busy):
            feeds.open(OTHER_MATCH)
        # Replacing the feed of a followed match is no new match.
        feeds.open(MATCH_ID)
        assert feeds.count == 1

    asyncio.run(scenario())


def test_shutdown_closes_streams_without_end():
    async def scenario():
        feeds = Feeds(GatewayConfig())
        watcher = feeds.open(MATCH_ID).watch(0)
        feeds.shutdown()
        assert drain(watcher) == [CLOSE]
        assert feeds.count == 0

    asyncio.run(scenario())
