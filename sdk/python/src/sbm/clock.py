"""Clock: the time situation of the current turn (spec/api/clock.json)."""

import time


class Clock:
    """Local view of the times from turn; the referee's clock is authoritative.

    Elapsed time is measured with a monotonic clock from the creation of the object, which the
    SDK does right after receiving turn.
    """

    __slots__ = ("_increment_ms", "_opponent_remaining_ms", "_remaining_ms", "_start_ns")

    def __init__(self, remaining_ms: int, opponent_remaining_ms: int, increment_ms: int) -> None:
        self._start_ns = time.monotonic_ns()
        self._remaining_ms = remaining_ms
        self._opponent_remaining_ms = opponent_remaining_ms
        self._increment_ms = increment_ms

    def remaining_ms(self) -> int:
        """Own remaining time at the start of this turn; does not decrease while thinking."""
        return self._remaining_ms

    def opponent_remaining_ms(self) -> int:
        """Remaining time of the opponent."""
        return self._opponent_remaining_ms

    def increment_ms(self) -> int:
        """Time added after each own move."""
        return self._increment_ms

    def elapsed_ms(self) -> int:
        """Time spent on this turn so far; keep a margin for the transport."""
        return (time.monotonic_ns() - self._start_ns) // 1_000_000

    def __repr__(self) -> str:
        return (
            f"Clock(remaining_ms={self._remaining_ms}, "
            f"opponent_remaining_ms={self._opponent_remaining_ms}, "
            f"increment_ms={self._increment_ms})"
        )
