"""Messages of gateway-v1 and relay-v1 (spec/protocol/gateway-v1, relay-v1), checked strictly."""

import hashlib
import json
import re

VERSION = 1
MAX_LINE_CHARS = 65_536

_MATCH_ID = re.compile(r"[0-9a-f]{24}")
_SEAT = re.compile(r"[A-Za-z0-9_-]{43}")
_SEAT_HASH = re.compile(r"[0-9a-f]{64}")


class InvalidMessage(ValueError):
    """A message does not follow the protocol."""


def seat_hash(seat: str) -> str:
    return hashlib.sha256(seat.encode("ascii")).hexdigest()


def _object(text: str | bytes) -> dict:
    try:
        message = json.loads(text)
    except (ValueError, UnicodeDecodeError):
        raise InvalidMessage("not JSON") from None
    if not isinstance(message, dict):
        raise InvalidMessage("not a JSON object")
    return message


def _exact(message: dict, kind: str, fields: dict[str, re.Pattern | None]) -> None:
    if message.get("type") != kind:
        raise InvalidMessage(f"expected {kind}")
    if set(message) != {"type", *fields}:
        raise InvalidMessage(f"{kind} must have exactly the fields type, {', '.join(fields)}")
    for name, pattern in fields.items():
        value = message[name]
        if pattern is None:
            if type(value) is not int or value != VERSION:
                raise InvalidMessage(f"{kind}: unsupported version {value!r}")
        elif not isinstance(value, str) or not pattern.fullmatch(value):
            raise InvalidMessage(f"{kind}: invalid {name}")


def parse_join(text: str | bytes) -> tuple[str, str]:
    """match_id and seat of a join message."""
    message = _object(text)
    _exact(message, "join", {"v": None, "match_id": _MATCH_ID, "seat": _SEAT})
    return message["match_id"], message["seat"]


def parse_attach(text: bytes) -> tuple[str, str]:
    """match_id and seat_hash of an attach line."""
    message = _object(text)
    _exact(message, "attach", {"v": None, "match_id": _MATCH_ID, "seat_hash": _SEAT_HASH})
    return message["match_id"], message["seat_hash"]


def parse_line(text: bytes) -> str:
    """The data of a line message from the runner."""
    message = _object(text)
    if message.get("type") != "line" or set(message) != {"type", "data"}:
        raise InvalidMessage("expected line with exactly the fields type, data")
    data = message["data"]
    if not isinstance(data, str) or len(data) > MAX_LINE_CHARS:
        raise InvalidMessage("line: data must be a string of at most 65536 characters")
    return data


def _encode(message: dict) -> str:
    return json.dumps(message, ensure_ascii=False, separators=(",", ":"))


def joined(match_id: str) -> str:
    return _encode({"type": "joined", "v": VERSION, "match_id": match_id})


def refused_client(code: str, text: str) -> str:
    return _encode({"type": "refused", "v": VERSION, "code": code, "message": text})


def refused_relay(code: str, text: str) -> bytes:
    return (_encode({"type": "refused", "code": code, "message": text}) + "\n").encode()


def relay_line(data: str) -> bytes:
    return (_encode({"type": "line", "data": data}) + "\n").encode()


PRESENT = b'{"type":"present"}\n'
ABSENT = b'{"type":"absent"}\n'
