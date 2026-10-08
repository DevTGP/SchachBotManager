"""Pairs each client with the game of its seat (gateway.md, relay-v1).

A session exists while the runner's relay connection for one seat is open. A client that joins
before the runner attaches waits; a client that joins a seat already taken replaces the older
connection. Lines for an absent client are kept and sent after it joins again.
"""

import asyncio
from collections import deque
from typing import Protocol

from sbm_gateway import messages
from sbm_gateway.config import GatewayConfig
from sbm_gateway.links import ClientGone

Key = tuple[str, str]  # match_id, seat_hash

# What join returns for a waiting client that a newer connection replaced, or on shutdown.
REPLACED = object()
SHUTDOWN = object()


class Client(Protocol):
    async def send(self, text: str) -> None: ...
    async def refuse(self, code: str, text: str, *, wait: bool = False) -> None: ...
    def end(self, reason: str) -> None: ...


class Relay(Protocol):
    async def send(self, line: bytes) -> None: ...
    def close(self) -> None: ...


class Refused(Exception):
    def __init__(self, code: str, text: str) -> None:
        super().__init__(text)
        self.code = code


class PendingOverflow(Exception):
    """An absent client missed more lines than the gateway keeps."""


class Session:
    def __init__(self, key: Key, relay: Relay, max_pending: int) -> None:
        self.key = key
        self.relay = relay
        self.client: Client | None = None
        self._pending: deque[str] = deque()
        self._max_pending = max_pending
        self._lock = asyncio.Lock()
        self.closed = False

    async def bind(self, client: Client) -> None:
        """Gives the seat to client: joined, the kept lines, then present to the runner."""
        async with self._lock:
            older, self.client = self.client, client
            if older is not None:
                await older.refuse("replaced", "a newer connection took this seat")
            try:
                await client.send(messages.joined(self.key[0]))
                while self._pending:
                    await client.send(self._pending[0])
                    self._pending.popleft()
            except ClientGone:
                self.client = None
                return
            await self.relay.send(messages.PRESENT)

    async def to_client(self, data: str) -> None:
        async with self._lock:
            if self.client is not None:
                try:
                    await self.client.send(data)
                    return
                except ClientGone:
                    pass  # its handler reports it absent; the line waits for the next client
            if len(self._pending) >= self._max_pending:
                raise PendingOverflow()
            self._pending.append(data)

    async def to_runner(self, client: Client, data: str) -> None:
        """Lines of a replaced client are dropped."""
        async with self._lock:
            if self.client is client and not self.closed:
                await self.relay.send(messages.relay_line(data))

    async def leave(self, client: Client) -> None:
        async with self._lock:
            if self.client is client and not self.closed:
                self.client = None
                await self.relay.send(messages.ABSENT)

    async def close(self, reason: str) -> None:
        async with self._lock:
            self.closed = True
            client, self.client = self.client, None
            self._pending.clear()
        if client is not None:
            client.end(reason)


class Registry:
    def __init__(self, config: GatewayConfig) -> None:
        self._config = config
        self._sessions: dict[Key, Session] = {}
        self._waiting: dict[Key, tuple[Client, asyncio.Future]] = {}
        self.clients = 0

    @property
    def session_count(self) -> int:
        return len(self._sessions)

    async def attach(self, key: Key, relay: Relay) -> Session:
        """Opens the session of a seat; raises Refused."""
        if key in self._sessions:
            raise Refused("attached", "another relay connection holds this seat")
        if len(self._sessions) >= self._config.max_sessions:
            raise Refused("busy", "the gateway holds too many games")
        session = Session(key, relay, self._config.max_pending_lines)
        self._sessions[key] = session
        waiting = self._waiting.pop(key, None)
        if waiting is not None:
            client, future = waiting
            await session.bind(client)
            future.set_result(session)
        return session

    async def detach(self, session: Session, reason: str) -> None:
        if self._sessions.get(session.key) is session:
            del self._sessions[session.key]
        await session.close(reason)

    async def join(self, key: Key, client: Client) -> Session | None | object:
        """The session client now holds, None if no runner attached in time, REPLACED or
        SHUTDOWN.
        """
        session = self._sessions.get(key)
        if session is not None:
            await session.bind(client)
            return session
        older = self._waiting.pop(key, None)
        if older is not None:
            older[1].set_result(REPLACED)
        future = asyncio.get_running_loop().create_future()
        self._waiting[key] = (client, future)
        await asyncio.wait({future}, timeout=self._config.join_wait_seconds)
        if future.done():
            return future.result()
        if self._waiting.get(key, (None, None))[1] is future:
            del self._waiting[key]
        future.cancel()
        return None

    async def shutdown(self) -> None:
        """Refuses waiting clients and ends every session."""
        for _client, future in self._waiting.values():
            if not future.done():
                future.set_result(SHUTDOWN)
        self._waiting.clear()
        for session in list(self._sessions.values()):
            session.relay.close()
            await self.detach(session, "the gateway stops")
