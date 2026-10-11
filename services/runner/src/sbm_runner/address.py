"""Addresses of the gateway as host:port, from the environment."""

from collections.abc import Mapping


def parse_address(name: str, text: str) -> tuple[str, int]:
    """name is the variable the text came from, for the error message."""
    host, _, port_text = text.rpartition(":")
    if not host or not port_text.isdigit() or not 1 <= int(port_text) <= 65535:
        raise ValueError(f"{name} must be host:port, not {text!r}")
    return host, int(port_text)


def live_address(environ: Mapping[str, str]) -> tuple[str, int] | None:
    """SBM_LIVE_ADDRESS, the gateway's live port (E142); None publishes no moves."""
    text = environ.get("SBM_LIVE_ADDRESS")
    return parse_address("SBM_LIVE_ADDRESS", text) if text else None
