"""Settings of a game are checked on creation."""

import pytest

from sbm.referee import STANDARD_FEN, MatchSettings


def test_defaults():
    settings = MatchSettings(initial_time_ms=60_000)
    assert settings.start_fen == STANDARD_FEN
    assert (settings.increment_ms, settings.tolerance_ms, settings.max_moves) == (0, 20, 500)
    assert settings.clock is True


def test_initial_time_is_required():
    with pytest.raises(TypeError):
        MatchSettings()


@pytest.mark.parametrize(
    ("fields", "error"),
    [
        ({"initial_time_ms": 0}, ValueError),
        ({"initial_time_ms": 2**53}, ValueError),
        ({"initial_time_ms": 1.0}, TypeError),
        ({"initial_time_ms": True}, TypeError),
        ({"increment_ms": -1}, ValueError),
        ({"startup_ms": 0}, ValueError),
        ({"tolerance_ms": -1}, ValueError),
        ({"max_moves": 0}, ValueError),
        ({"memory_limit_mib": 0}, ValueError),
        ({"game_id": "a b"}, ValueError),
        ({"game_id": "x" * 65}, ValueError),
        ({"game_id": "x\n"}, ValueError),
        ({"discipline": ""}, ValueError),
        ({"discipline": "x" * 65}, ValueError),
        ({"clock": 1}, TypeError),
        ({"start_fen": "8/8/8/8/8/8/8/8 w - - 0 1"}, ValueError),
        ({"start_fen": None}, ValueError),
    ],
)
def test_invalid(fields, error):
    with pytest.raises(error):
        MatchSettings(**({"initial_time_ms": 1000} | fields))


def test_limits_are_accepted():
    MatchSettings(
        initial_time_ms=2**53 - 1,
        tolerance_ms=0,
        max_moves=1,
        game_id="A-z_9" + "x" * 59,
        discipline="x" * 64,
        clock=False,
    )
