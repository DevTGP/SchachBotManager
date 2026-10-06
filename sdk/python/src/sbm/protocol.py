"""Messages of protocol version 1 (spec/protocol/v1/); unknown referee fields are ignored (E36)."""

from sbm.channel import ProtocolError
from sbm.constants import BLACK, WHITE
from sbm.info import info_fields
from sbm.records import GameInfo, GameResult, Info

PROTOCOL_VERSION = 1
LANGUAGE = "python"
COLORS = {"white": WHITE, "black": BLACK}


def field(message: dict, name: str, kind: type | tuple[type, ...]) -> object:
    """A required field of a referee message with its JSON type."""
    value = message.get(name)
    # bool is an int in Python but not in JSON.
    if not isinstance(value, kind) or isinstance(value, bool):
        raise ProtocolError(f"{message.get('type')}: field {name!r} missing or not {kind}")
    return value


def game_info(init: dict) -> GameInfo:
    color = field(init, "color", str)
    if color not in COLORS:
        raise ProtocolError(f"init: unknown color {color!r}")
    return GameInfo(
        game_id=field(init, "game_id", str),
        color=COLORS[color],
        opponent_name=field(init, "opponent_name", str),
        start_fen=field(init, "start_fen", str),
        initial_time_ms=field(init, "initial_time_ms", int),
        increment_ms=field(init, "increment_ms", int),
        startup_ms=field(init, "startup_ms", int),
        memory_limit_mib=field(init, "memory_limit_mib", int),
        discipline=field(init, "discipline", str),
    )


def supported_versions(init: dict) -> list:
    return field(init, "supported", list)


def game_result(game_over: dict) -> GameResult:
    return GameResult(
        result=field(game_over, "result", str),
        termination=field(game_over, "termination", str),
    )


def ready(sdk_version: str) -> dict:
    return {"type": "ready", "v": PROTOCOL_VERSION, "sdk": sdk_version, "lang": LANGUAGE}


def resign() -> dict:
    return {"type": "resign", "v": PROTOCOL_VERSION}


def move(uci: str, info: Info | None) -> dict:
    message = {"type": "move", "v": PROTOCOL_VERSION, "move": uci}
    if info is not None:
        message["info"] = info_fields(info)
    return message
