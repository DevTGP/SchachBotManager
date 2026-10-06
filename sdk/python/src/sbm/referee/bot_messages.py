"""Strict reading of bot lines against spec/protocol/v1 (bot_message.schema.json, E66).

Bot output is hostile input. This module accepts exactly what the schemas accept; the tests
compare its verdict with a JSON Schema validator on the protocol examples and on edge cases.
"""

import json
import re
from dataclasses import dataclass

PROTOCOL_VERSION = 1
SUPPORTED_VERSIONS = [PROTOCOL_VERSION]

UCI = re.compile(r"[a-h][1-8][a-h][1-8][nbrq]?")
SDK_VERSION = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?"
)
LANGUAGES = frozenset({"python", "cpp", "java", "csharp", "javascript"})
MAX_SDK_LENGTH = 64

# Field: inclusive range from move.schema.json
INFO_INTEGERS = {
    "depth": (0, 1024),
    "seldepth": (0, 1024),
    "score_cp": (-100_000, 100_000),
    "score_mate": (-1024, 1024),
    "nodes": (0, 2**53 - 1),
}
INFO_FIELDS = frozenset(INFO_INTEGERS) | {"pv", "text"}
MAX_PV_MOVES = 32
MAX_TEXT_LENGTH = 256
MAX_INTEGER_DIGITS = 64


class Violation(Exception):
    """A line breaks the protocol; code is one of the error codes of error.schema.json."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class Ready:
    version: int
    sdk: str
    lang: str


@dataclass(frozen=True)
class MoveMessage:
    uci: str
    info: dict | None


@dataclass(frozen=True)
class Resign:
    pass


BotMessage = Ready | MoveMessage | Resign


def read(line: bytes) -> BotMessage:
    """The message in one line without its line end; raises Violation."""
    try:
        message = json.loads(
            line.decode("utf-8"), parse_constant=_reject_constant, parse_int=_parse_int
        )
    except (UnicodeDecodeError, ValueError) as error:
        raise Violation("invalid_json", f"invalid JSON: {error}") from None
    except RecursionError:
        # Valid JSON, but no bot message nests deeper than three levels.
        raise Violation("schema_violation", "the message is nested too deeply") from None
    if not isinstance(message, dict):
        raise Violation("schema_violation", "a message must be a JSON object")
    kind = message.get("type")
    if not isinstance(kind, str):
        raise Violation("schema_violation", "field 'type' missing or not a string")
    if kind == "ready":
        return _ready(message)
    if kind == "move":
        return _move(message)
    if kind == "resign":
        _fields(message, required={"type", "v"})
        _version(message)
        return Resign()
    raise Violation("unknown_type", f"a bot cannot send messages of type {kind[:64]!r}")


def _reject_constant(name: str) -> None:
    # Python reads NaN and Infinity, JSON does not know them.
    raise ValueError(f"{name} is not JSON")


def _parse_int(text: str) -> int | float:
    # Python refuses to convert integers of more than 4300 digits. No field allows integers
    # beyond 2**53, so long ones become floats, which the range checks reject.
    return int(text) if len(text) <= MAX_INTEGER_DIGITS else float(text)


def _ready(message: dict) -> Ready:
    _fields(message, required={"type", "v", "sdk", "lang"})
    version = integer(message["v"])
    if version is not None and version not in SUPPORTED_VERSIONS:
        raise Violation(
            "unsupported_version",
            f"ready: version {version} is not one of the supported {SUPPORTED_VERSIONS}",
        )
    _version(message)
    sdk = message["sdk"]
    if not isinstance(sdk, str) or len(sdk) > MAX_SDK_LENGTH or not SDK_VERSION.fullmatch(sdk):
        raise _schema("ready", "sdk", "is not a SemVer version")
    lang = message["lang"]
    if not isinstance(lang, str) or lang not in LANGUAGES:
        raise _schema("ready", "lang", f"is not one of {sorted(LANGUAGES)}")
    return Ready(version=PROTOCOL_VERSION, sdk=sdk, lang=lang)


def _move(message: dict) -> MoveMessage:
    _fields(message, required={"type", "v", "move"}, optional={"info"})
    _version(message)
    if not is_uci(message["move"]):
        raise _schema("move", "move", "is not a move in UCI notation")
    info = _info(message["info"]) if "info" in message else None
    return MoveMessage(uci=message["move"], info=info)


def _info(info: object) -> dict:
    if not isinstance(info, dict):
        raise _schema("move", "info", "is not an object")
    unknown = info.keys() - INFO_FIELDS
    if unknown:
        raise _schema("move", "info", f"has unknown fields {sorted(unknown)}")
    if "score_cp" in info and "score_mate" in info:
        raise _schema("move", "info", "has both score_cp and score_mate")
    fields: dict = {}
    for name, (low, high) in INFO_INTEGERS.items():
        if name not in info:
            continue
        number = integer(info[name])
        if number is None or not low <= number <= high or (name == "score_mate" and number == 0):
            raise _schema("move", f"info.{name}", f"is not an integer in {low}..{high}")
        fields[name] = number
    if "pv" in info:
        pv = info["pv"]
        if not isinstance(pv, list) or len(pv) > MAX_PV_MOVES or not all(map(is_uci, pv)):
            raise _schema("move", "info.pv", f"is not a list of at most {MAX_PV_MOVES} UCI moves")
        fields["pv"] = pv
    if "text" in info:
        text = info["text"]
        if not isinstance(text, str) or len(text) > MAX_TEXT_LENGTH:
            raise _schema("move", "info.text", f"is not a string of at most {MAX_TEXT_LENGTH}")
        fields["text"] = text
    return fields


def _fields(message: dict, required: set[str], optional: frozenset[str] = frozenset()) -> None:
    kind = message["type"]
    missing = required - message.keys()
    if missing:
        raise Violation("schema_violation", f"{kind}: missing fields {sorted(missing)}")
    unknown = message.keys() - required - optional
    if unknown:
        names = sorted(name[:64] for name in unknown)[:8]
        raise Violation("schema_violation", f"{kind}: unknown fields {names}")


def _version(message: dict) -> None:
    if integer(message["v"]) != PROTOCOL_VERSION:
        raise _schema(message["type"], "v", f"is not {PROTOCOL_VERSION}")


def _schema(kind: str, field: str, problem: str) -> Violation:
    return Violation("schema_violation", f"{kind}: field {field!r} {problem}")


def integer(value: object) -> int | None:
    """The value as a JSON Schema integer: 3 and 3.0 count, true does not."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def is_uci(value: object) -> bool:
    return isinstance(value, str) and UCI.fullmatch(value) is not None
