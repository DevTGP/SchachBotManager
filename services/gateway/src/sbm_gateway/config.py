"""Addresses and limits of the gateway, from the environment as in the container."""

import re
from collections.abc import Mapping
from dataclasses import dataclass

# The WebSocket endpoint behind the frontend's nginx (gateway-v1).
SOCKET_PATH = "/api/v1/play/socket"
# The event stream of a running match, also behind the frontend's nginx (E142).
WATCH_PATH = re.compile(r"/api/v1/matches/([0-9a-f]{24})/live")


@dataclass(frozen=True)
class GatewayConfig:
    """relay_host is the gateway's own name on the relay network; only the play runner can reach
    that address, so the relay needs no secret (E112).
    """

    socket_host: str = "0.0.0.0"
    socket_port: int = 8001
    relay_host: str = "127.0.0.1"
    relay_port: int = 9000
    # A client waits this long for the runner to attach its seat before no_game.
    join_wait_seconds: float = 30.0
    # Time for the first message of a connection, join or attach.
    hello_seconds: float = 10.0
    max_sessions: int = 32
    max_clients: int = 128
    # Lines kept for an absent client; beyond that the game cannot be resumed and ends.
    max_pending_lines: int = 256
    ping_seconds: float = 20.0
    # Live channel (E102, E142): runners send moves to the live port, viewers read them as
    # server-sent events from the watch port. live_host is the gateway's name on the live network.
    live_host: str = "127.0.0.1"
    live_port: int = 9001
    watch_host: str = "0.0.0.0"
    watch_port: int = 8002
    max_feeds: int = 16
    max_watchers: int = 256
    # Moves kept per match; a longer game ends its feed and the viewers ask the API again.
    max_feed_moves: int = 4096
    # A viewer that asks for a match not published yet waits this long, e.g. at the start.
    feed_wait_seconds: float = 5.0
    # A comment line this often keeps idle event streams open through the proxies.
    watch_ping_seconds: float = 15.0

    @classmethod
    def from_env(cls, environ: Mapping[str, str]) -> "GatewayConfig":
        defaults = cls()
        return cls(
            socket_port=_port(environ, "SBM_GATEWAY_PORT", defaults.socket_port),
            relay_host=environ.get("SBM_RELAY_HOST") or defaults.relay_host,
            relay_port=_port(environ, "SBM_RELAY_PORT", defaults.relay_port),
            max_sessions=_positive(environ, "SBM_GATEWAY_MAX_SESSIONS", defaults.max_sessions),
            max_clients=_positive(environ, "SBM_GATEWAY_MAX_CLIENTS", defaults.max_clients),
            live_host=environ.get("SBM_LIVE_HOST") or defaults.live_host,
            live_port=_port(environ, "SBM_LIVE_PORT", defaults.live_port),
            watch_port=_port(environ, "SBM_WATCH_PORT", defaults.watch_port),
            max_watchers=_positive(environ, "SBM_GATEWAY_MAX_WATCHERS", defaults.max_watchers),
        )


def _positive(environ: Mapping[str, str], name: str, default: int) -> int:
    text = environ.get(name)
    if not text:
        return default
    if not text.isdigit() or int(text) < 1:
        raise ValueError(f"{name} must be a positive whole number, not {text!r}")
    return int(text)


def _port(environ: Mapping[str, str], name: str, default: int) -> int:
    port = _positive(environ, name, default)
    if port > 65535:
        raise ValueError(f"{name} must be a port from 1 to 65535, not {port}")
    return port
