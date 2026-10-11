import json
from pathlib import Path

import pytest
from conftest import MATCH_ID, move

from sbm_gateway import live_messages
from sbm_gateway.messages import InvalidMessage

EXAMPLES = Path(__file__).parents[3] / "spec" / "protocol" / "live-v1" / "examples"


def parse(line: bytes):
    if json.loads(line).get("type") == "open":
        return live_messages.parse_open(line)
    return live_messages.parse_line(line)


@pytest.mark.parametrize("path", sorted((EXAMPLES / "valid").glob("*.json")), ids=lambda p: p.name)
def test_the_valid_examples_of_the_spec_are_read(path):
    parse(path.read_bytes())


@pytest.mark.parametrize(
    "path", sorted((EXAMPLES / "invalid").glob("*.json")), ids=lambda p: p.name
)
def test_the_invalid_examples_of_the_spec_are_refused(path):
    with pytest.raises(InvalidMessage):
        parse(path.read_bytes())


def test_open_gives_the_match():
    line = json.dumps({"type": "open", "v": 1, "match_id": MATCH_ID}).encode()
    assert live_messages.parse_open(line) == MATCH_ID


def test_a_move_passes_unchanged():
    assert live_messages.parse_line(json.dumps({"type": "move", "move": move(3)}).encode()) == (
        "move",
        move(3),
    )


@pytest.mark.parametrize("ply", [0, -1, 1.0, True, "1"])
def test_a_move_needs_a_whole_ply_from_one(ply):
    line = json.dumps({"type": "move", "move": {**move(1), "ply": ply}}).encode()
    with pytest.raises(InvalidMessage):
        live_messages.parse_line(line)


@pytest.mark.parametrize("line", [b"open", b"[]", b"\xff\n"])
def test_no_json_object_is_refused(line):
    with pytest.raises(InvalidMessage):
        live_messages.parse_open(line)
    with pytest.raises(InvalidMessage):
        live_messages.parse_line(line)
