import json

import pytest
from conftest import MATCH_ID, SEAT

from sbm_gateway import messages


def test_join_is_read_strictly():
    text = json.dumps({"type": "join", "v": 1, "match_id": MATCH_ID, "seat": SEAT})
    assert messages.parse_join(text) == (MATCH_ID, SEAT)


@pytest.mark.parametrize(
    "message",
    [
        {"type": "join", "v": 2, "match_id": MATCH_ID, "seat": SEAT},
        {"type": "join", "v": True, "match_id": MATCH_ID, "seat": SEAT},
        {"type": "join", "v": 1, "match_id": MATCH_ID.upper(), "seat": SEAT},
        {"type": "join", "v": 1, "match_id": MATCH_ID, "seat": SEAT[:-1]},
        {"type": "join", "v": 1, "match_id": MATCH_ID, "seat": SEAT, "extra": 1},
        {"type": "attach", "v": 1, "match_id": MATCH_ID, "seat": SEAT},
        [],
    ],
)
def test_invalid_joins_are_refused(message):
    with pytest.raises(messages.InvalidMessage):
        messages.parse_join(json.dumps(message))


def test_no_json_is_refused():
    with pytest.raises(messages.InvalidMessage):
        messages.parse_join("join please")


def test_a_trailing_newline_is_no_valid_seat():
    with pytest.raises(messages.InvalidMessage):
        messages.parse_join(
            json.dumps({"type": "join", "v": 1, "match_id": MATCH_ID, "seat": SEAT[:-1] + "\n"})
        )


def test_attach_carries_the_hash_not_the_seat():
    hashed = messages.seat_hash(SEAT)
    line = json.dumps({"type": "attach", "v": 1, "match_id": MATCH_ID, "seat_hash": hashed})
    assert messages.parse_attach(line.encode()) == (MATCH_ID, hashed)
    assert len(hashed) == 64


def test_line_data_is_limited():
    assert messages.parse_line(b'{"type":"line","data":"x"}') == "x"
    too_long = json.dumps({"type": "line", "data": "x" * 65_537}).encode()
    with pytest.raises(messages.InvalidMessage):
        messages.parse_line(too_long)
    with pytest.raises(messages.InvalidMessage):
        messages.parse_line(b'{"type":"line","data":{}}')


def test_built_messages_follow_the_spec():
    assert json.loads(messages.joined(MATCH_ID)) == {"type": "joined", "v": 1, "match_id": MATCH_ID}
    assert json.loads(messages.relay_line('{"a":"ü"}')) == {"type": "line", "data": '{"a":"ü"}'}
    assert messages.PRESENT.endswith(b"\n") and messages.ABSENT.endswith(b"\n")
