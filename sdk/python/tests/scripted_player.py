"""A player that answers from a script, on a fake clock, for tests of the referee."""

import json
from dataclasses import dataclass

from sbm.referee import Player, PlayerClosed, PlayerTimeout

NS_PER_MS = 1_000_000


class FakeTime:
    """Monotonic nanoseconds that only move when a scripted answer takes time."""

    def __init__(self) -> None:
        self.ns = 0

    def __call__(self) -> int:
        return self.ns


@dataclass
class Reply:
    """One line after after_ms. Without waiting the line is lost if it comes after the
    deadline; with waiting it is returned anyway, as an adapter returns a buffered line.
    """

    line: dict | bytes
    after_ms: int = 0
    waiting: bool = False


@dataclass
class Early:
    """A line the bot sent outside its turn; the referee finds it when it polls."""

    line: dict | bytes


def ready(**fields) -> dict:
    return {"type": "ready", "v": 1, "sdk": "1.0.0", "lang": "python"} | fields


def move(uci: str, **info) -> dict:
    message = {"type": "move", "v": 1, "move": uci}
    if info:
        message["info"] = info
    return message


def resign() -> dict:
    return {"type": "resign", "v": 1}


class ScriptedPlayer(Player):
    """Each receive takes the next script item: a dict or bytes is answered at once, a Reply
    after its time, an exception is raised. events records every call of the referee.
    """

    def __init__(self, name: str, time: FakeTime, script: list) -> None:
        super().__init__(name)
        self.time = time
        self.script = list(script)
        self.events: list[tuple] = []
        self.alive = True

    @property
    def sent(self) -> list[dict]:
        return [event[1] for event in self.events if event[0] == "send"]

    def sent_types(self) -> list[str]:
        return [message["type"] for message in self.sent]

    def start(self) -> None:
        self.events.append(("start",))

    def send(self, message: dict) -> None:
        if not self.alive:
            raise PlayerClosed("already gone")
        self.events.append(("send", json.loads(json.dumps(message))))

    def receive(self, deadline_ns: int | None) -> bytes:
        self.events.append(("receive", deadline_ns))
        item = self.script[0] if self.script else None
        polling = deadline_ns is not None and deadline_ns <= self.time.ns
        if polling and not isinstance(item, Early):
            raise PlayerTimeout()
        if item is None:
            raise AssertionError(f"{self.name}: script exhausted")
        self.script.pop(0)
        if isinstance(item, BaseException):
            if isinstance(item, PlayerClosed):
                self.alive = False
            raise item
        if not isinstance(item, Reply | Early):
            item = Reply(item)
        if isinstance(item, Reply):
            self.time.ns += item.after_ms * NS_PER_MS
            if deadline_ns is not None and self.time.ns > deadline_ns and not item.waiting:
                self.time.ns = deadline_ns
                raise PlayerTimeout()
        line = item.line
        return line if isinstance(line, bytes) else json.dumps(line).encode()

    def suspend(self) -> None:
        self.events.append(("suspend",))

    def resume(self) -> None:
        if not self.alive:
            raise PlayerClosed("already gone")
        self.events.append(("resume",))

    def close(self) -> None:
        self.events.append(("close",))
