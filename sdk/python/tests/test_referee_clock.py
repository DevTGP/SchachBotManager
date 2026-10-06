"""The referee's clock: deadlines, tolerance, increment, switched off."""

import pytest

from sbm import BLACK, WHITE
from sbm.referee import MatchSettings
from sbm.referee.clock import GameClock, elapsed_ms

MS = 1_000_000


def clock(**settings) -> GameClock:
    return GameClock(MatchSettings(**({"initial_time_ms": 1000} | settings)))


def test_deadline():
    game_clock = clock(tolerance_ms=20)
    assert game_clock.deadline_ns(WHITE, 5 * MS) == 1025 * MS


def test_charge_and_increment():
    game_clock = clock(increment_ms=100, tolerance_ms=20)
    game_clock.charge(WHITE, 300)
    assert game_clock.remaining_ms(WHITE) == 800
    assert game_clock.remaining_ms(BLACK) == 1000
    game_clock.charge(WHITE, 820)
    assert game_clock.remaining_ms(WHITE) == 100


def test_over_the_time():
    game_clock = clock(tolerance_ms=20)
    assert not game_clock.is_over(BLACK, 1020)
    assert game_clock.is_over(BLACK, 1021)
    with pytest.raises(ValueError):
        game_clock.charge(BLACK, 1021)
    game_clock.flag(BLACK)
    assert game_clock.remaining_ms(BLACK) == 0


def test_switched_off():
    game_clock = clock(clock=False)
    assert not game_clock.running
    assert game_clock.deadline_ns(WHITE, 0) is None
    assert not game_clock.is_over(WHITE, 10**12)
    game_clock.charge(WHITE, 10**12)
    assert game_clock.remaining_ms(WHITE) == 1000


def test_elapsed_rounds_down():
    assert elapsed_ms(0, 2 * MS - 1) == 1
    assert elapsed_ms(10, 10) == 0
