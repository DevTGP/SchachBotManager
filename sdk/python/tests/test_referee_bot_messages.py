"""Strict reading of bot lines agrees with the protocol schemas (E66)."""

import json

import pytest
from protocol_schemas import PROTOCOL, violations

from sbm.referee.bot_messages import MoveMessage, Ready, Resign, Violation, read

BOT_MESSAGE_PREFIXES = ("bot_message", "ready", "move", "resign")


def example_paths(kind: str) -> list:
    return sorted(
        path
        for prefix in BOT_MESSAGE_PREFIXES
        for path in (PROTOCOL / "examples" / kind).glob(f"{prefix}.*.json")
    )


def line(message: object) -> bytes:
    return json.dumps(message, ensure_ascii=False).encode()


def accepts(message: object) -> bool:
    try:
        read(line(message))
    except Violation:
        return False
    return True


@pytest.mark.parametrize("path", example_paths("valid"), ids=lambda path: path.stem)
def test_valid_examples_are_accepted(path):
    message = json.loads(path.read_text("utf-8"))
    assert accepts(message)


@pytest.mark.parametrize("path", example_paths("invalid"), ids=lambda path: path.stem)
def test_invalid_examples_are_rejected(path):
    message = json.loads(path.read_text("utf-8"))
    assert not accepts(message)


def ready(**fields):
    return {"type": "ready", "v": 1, "sdk": "1.0.0", "lang": "python"} | fields


def move(**fields):
    return {"type": "move", "v": 1, "move": "e2e4"} | fields


def info(**fields):
    return move(info=fields)


EDGE_CASES = [
    # Integers as JSON Schema sees them
    move(v=1.0),
    move(v=True),
    move(v="1"),
    move(v=2),
    ready(v=1.0),
    ready(v=2),
    ready(v=False),
    info(depth=3.0),
    info(depth=3.5),
    info(depth=True),
    info(depth=-1),
    info(depth=1024),
    info(depth=1025),
    info(seldepth=0),
    info(nodes=2**53 - 1),
    info(nodes=2**53),
    info(score_cp=-100_000),
    info(score_cp=100_001),
    info(score_mate=0),
    info(score_mate=-1),
    info(score_mate=1025),
    info(score_cp=1, score_mate=1),
    # Strings and patterns
    move(move="e7e8q"),
    move(move="e7e8k"),
    move(move="e2e4 "),
    move(move="e2e4\n"),
    move(move="0000"),
    move(move=None),
    ready(sdk="1.2.3-rc.1+build.5"),
    ready(sdk="01.2.3"),
    ready(sdk="1.2"),
    ready(sdk="1.2.3\n"),
    ready(sdk="1." + "1" * 62),
    ready(sdk="1.0." + "1" * 61),
    ready(lang="Python"),
    ready(lang=["python"]),
    info(text=""),
    info(text="ä" * 256),
    info(text="😀" * 256),
    info(text="x" * 257),
    info(text=None),
    info(pv=[]),
    info(pv=["e2e4"] * 32),
    info(pv=["e2e4"] * 33),
    info(pv="e2e4"),
    info(pv=["e2e4", 5]),
    # Structure
    {},
    [],
    "move",
    None,
    {"type": 1},
    {"type": "init"},
    {"type": "resign", "v": 1},
    {"type": "resign", "v": 1, "reason": "lost"},
    {"type": "resign"},
    move(info={}),
    move(info=None),
    move(info=[]),
    info(unknown=1),
    {"v": 1, "move": "e2e4"},
]


@pytest.mark.parametrize("message", EDGE_CASES, ids=lambda message: repr(message)[:80])
def test_agrees_with_the_schema(message):
    assert accepts(message) == (violations("bot_message", message) == [])


@pytest.mark.parametrize(
    ("raw", "code"),
    [
        (b"{", "invalid_json"),
        (b"", "invalid_json"),
        (b"\xff\xfe", "invalid_json"),
        (b'{"type":"move","v":NaN,"move":"e2e4"}', "invalid_json"),
        (b'{"type":"move","v":Infinity,"move":"e2e4"}', "invalid_json"),
        (b'{"type":"move","v":1} {}', "invalid_json"),
        (b"[" * 100_000 + b"]" * 100_000, "schema_violation"),
        (b'{"a":' * 50_000 + b"1" + b"}" * 50_000, "schema_violation"),
        (b'{"type":"move","v":1' + b"0" * 5000 + b',"move":"e2e4"}', "schema_violation"),
        (b'{"type":"move","v":1e400,"move":"e2e4"}', "schema_violation"),
        (b'{"type":"draw","v":1}', "unknown_type"),
        (b'{"type":"init"}', "unknown_type"),
        (b'{"type":"ready","v":2,"sdk":"1.0.0","lang":"python"}', "unsupported_version"),
        (b'{"type":"ready","v":"2","sdk":"1.0.0","lang":"python"}', "schema_violation"),
        (b'{"type":"move","v":2,"move":"e2e4"}', "schema_violation"),
    ],
    ids=lambda value: repr(value[:40]),
)
def test_violation_codes(raw, code):
    with pytest.raises(Violation) as caught:
        read(raw)
    assert caught.value.code == code
    assert len(caught.value.message) < 400


def test_messages():
    assert read(line(ready(v=1.0))) == Ready(version=1, sdk="1.0.0", lang="python")
    assert read(b'{"type":"resign","v":1}') == Resign()
    assert read(line(move())) == MoveMessage(uci="e2e4", info=None)
    full = {"depth": 5.0, "seldepth": 9, "score_mate": -3, "nodes": 10, "pv": [], "text": "hi"}
    assert read(line(move(info=full))).info == full | {"depth": 5}
    assert type(read(line(move(info=full))).info["depth"]) is int


def test_duplicate_keys_use_the_last_value():
    assert read(b'{"type":"move","v":1,"move":"zz","move":"e2e4"}').uci == "e2e4"
