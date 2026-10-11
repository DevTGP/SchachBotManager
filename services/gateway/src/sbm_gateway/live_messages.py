"""Lines of live-v1 from the runners (spec/protocol/live-v1), checked strictly."""

import json
import re
from typing import Literal

from sbm_gateway.messages import VERSION, InvalidMessage

_MATCH_ID = re.compile(r"[0-9a-f]{24}")
MOVE_FIELDS = frozenset({"ply", "uci", "san", "fen", "spent_ms", "clock_ms", "info"})


def _object(line: bytes) -> dict:
    try:
        message = json.loads(line)
    except (ValueError, UnicodeDecodeError):
        raise InvalidMessage("not JSON") from None
    if not isinstance(message, dict):
        raise InvalidMessage("not a JSON object")
    return message


def parse_open(line: bytes) -> str:
    """The match_id of an open line."""
    message = _object(line)
    if message.get("type") != "open" or set(message) != {"type", "v", "match_id"}:
        raise InvalidMessage("expected open with exactly the fields type, v, match_id")
    version, match_id = message["v"], message["match_id"]
    if type(version) is not int or version != VERSION:
        raise InvalidMessage(f"open: unsupported version {version!r}")
    if not isinstance(match_id, str) or not _MATCH_ID.fullmatch(match_id):
        raise InvalidMessage("open: invalid match_id")
    return match_id


def parse_line(line: bytes) -> tuple[Literal["move"], dict] | tuple[Literal["end"], None]:
    """A move with its fields, or the end. The runner is trusted with the content of a move;
    the gateway checks its shape and passes it on unchanged.
    """
    message = _object(line)
    kind = message.get("type")
    if kind == "end" and set(message) == {"type"}:
        return "end", None
    if kind != "move" or set(message) != {"type", "move"}:
        raise InvalidMessage("expected move with exactly the fields type, move, or end")
    move = message["move"]
    if not isinstance(move, dict) or set(move) != MOVE_FIELDS:
        raise InvalidMessage(f"move: needs exactly the fields {', '.join(sorted(MOVE_FIELDS))}")
    ply = move["ply"]
    if type(ply) is not int or ply < 1:
        raise InvalidMessage("move: ply must be a whole number from 1")
    return "move", move
