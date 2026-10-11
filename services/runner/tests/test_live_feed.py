import json
import threading
import time

from live_listener import LiveListener

from sbm_runner.live_feed import LiveFeed

MATCH = "65f0c0ffee0000000000abcd"
OPEN = {"type": "open", "v": 1, "match_id": MATCH}
END = {"type": "end"}


def move(ply: int) -> dict:
    return {"ply": ply, "uci": "e2e4", "san": "e4", "fen": "fen", "spent_ms": 5, "clock_ms": 995}


def moved(ply: int) -> dict:
    return {"type": "move", "move": move(ply)}


def wait_for(predicate, seconds: float = 5) -> None:
    deadline = time.monotonic() + seconds
    while not predicate():
        assert time.monotonic() < deadline, "timed out"
        time.sleep(0.01)


class FakeConnection:
    """Records what the feed sends; fail_after breaks the connection after that many sends."""

    def __init__(self, fail_after: int | None = None) -> None:
        self.sent: list[bytes] = []
        self.closed = False
        self._fail_after = fail_after

    def sendall(self, data: bytes) -> None:
        if self._fail_after is not None and len(self.sent) >= self._fail_after:
            raise ConnectionResetError("gone")
        self.sent.append(data)

    def close(self) -> None:
        self.closed = True

    def lines(self) -> list[dict]:
        return [json.loads(line) for line in b"".join(self.sent).splitlines()]


class FakeGateway:
    """connect for the feed: hands out the given connections, an exception is raised instead."""

    def __init__(self, *outcomes) -> None:
        self._outcomes = list(outcomes)
        self.calls: list[tuple] = []

    def __call__(self, address, timeout):
        self.calls.append((address, timeout))
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def test_without_an_address_nothing_happens():
    gateway = FakeGateway()
    feed = LiveFeed(None, MATCH, connect=gateway)

    feed.open()
    feed.move(move(1))
    feed.end()

    assert gateway.calls == []


def test_sends_open_the_moves_and_end():
    connection = FakeConnection()
    gateway = FakeGateway(connection)
    feed = LiveFeed(("sbm-live", 9001), MATCH, connect=gateway, connect_timeout=1.5)

    feed.open()
    feed.move(move(1))
    feed.move(move(2))
    feed.end()

    assert gateway.calls == [(("sbm-live", 9001), 1.5)]
    assert connection.lines() == [OPEN, moved(1), moved(2), END]
    assert connection.closed


def test_a_gateway_that_comes_later_gets_the_earlier_moves():
    connection = FakeConnection()
    gateway = FakeGateway(ConnectionRefusedError("not yet"), connection)
    feed = LiveFeed(("sbm-live", 9001), MATCH, connect=gateway, retry_seconds=0.05)

    feed.open()
    feed.move(move(1))
    wait_for(lambda: len(gateway.calls) == 2)
    feed.move(move(2))
    feed.end()

    assert connection.lines() == [OPEN, moved(1), moved(2), END]


def test_a_broken_connection_is_opened_again_with_every_move():
    broken = FakeConnection(fail_after=2)
    fresh = FakeConnection()
    gateway = FakeGateway(broken, fresh)
    feed = LiveFeed(("sbm-live", 9001), MATCH, connect=gateway, retry_seconds=0.05)

    feed.open()
    feed.move(move(1))
    feed.move(move(2))
    wait_for(lambda: len(gateway.calls) == 2)
    feed.move(move(3))
    feed.end()

    assert broken.lines() == [OPEN, moved(1)]
    assert broken.closed
    assert fresh.lines() == [OPEN, moved(1), moved(2), moved(3), END]


def test_end_without_a_gateway_sends_nothing_and_returns():
    gateway = FakeGateway(ConnectionRefusedError("down"))
    feed = LiveFeed(("sbm-live", 9001), MATCH, connect=gateway, retry_seconds=60)

    feed.open()
    feed.move(move(1))
    started = time.monotonic()
    feed.end()

    assert time.monotonic() - started < 1
    assert len(gateway.calls) == 1


def test_a_hanging_gateway_does_not_hold_up_the_end():
    release = threading.Event()

    def hanging(address, timeout):
        release.wait(10)
        raise TimeoutError("timed out")

    feed = LiveFeed(("sbm-live", 9001), MATCH, connect=hanging, end_wait=0.1)
    feed.open()
    feed.move(move(1))
    started = time.monotonic()
    feed.end()
    release.set()

    assert time.monotonic() - started < 1


def test_over_a_real_connection():
    listener = LiveListener()
    try:
        feed = LiveFeed(listener.address, MATCH)
        feed.open()
        feed.move(move(1))
        feed.end()
        listener.wait_closed()
    finally:
        listener.close()

    assert listener.connections == [[OPEN, moved(1), END]]
