"""Time controls on the command line and in PGN."""

import pytest

from sbm.arena.time_control import TimeControlError, format_time_control, parse_time_control


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("60+1", (60_000, 1_000)),
        ("300", (300_000, 0)),
        ("0.5+0.1", (500, 100)),
        ("1.25+0", (1_250, 0)),
        (" 10+0.005 ", (10_000, 5)),
    ],
)
def test_parse(text, expected):
    assert parse_time_control(text) == expected


@pytest.mark.parametrize("text", ["", "0", "0+1", "-1+0", "60+", "+1", "1.2345", "1,5", "a+b"])
def test_invalid(text):
    with pytest.raises(TimeControlError):
        parse_time_control(text)


@pytest.mark.parametrize(
    ("initial", "increment", "expected"),
    [(60_000, 1_000, "60+1"), (500, 0, "0.5+0"), (1_250, 5, "1.25+0.005")],
)
def test_format(initial, increment, expected):
    assert format_time_control(initial, increment) == expected
    assert parse_time_control(expected) == (initial, increment)
