"""Clock: values from turn and locally measured elapsed time (spec/api/clock.json)."""

import time

import sbm


def test_values():
    clock = sbm.Clock(300_000, 299_000, 2_000)
    assert clock.remaining_ms() == 300_000
    assert clock.opponent_remaining_ms() == 299_000
    assert clock.increment_ms() == 2_000
    assert repr(clock) == (
        "Clock(remaining_ms=300000, opponent_remaining_ms=299000, increment_ms=2000)"
    )


def test_elapsed_time():
    clock = sbm.Clock(1_000, 1_000, 0)
    assert 0 <= clock.elapsed_ms() < 1_000
    time.sleep(0.05)
    assert clock.elapsed_ms() >= 40
    assert clock.remaining_ms() == 1_000
