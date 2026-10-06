"""The referee's chess clock in wall-clock time (E19, match-runner.md)."""

from sbm.referee.settings import MatchSettings

NANOSECONDS_PER_MS = 1_000_000


class GameClock:
    """Remaining time of both sides; the time of a turn runs from sending turn to receiving move.

    Times are monotonic nanoseconds from the caller, so the clock itself never reads the time.
    A turn may exceed the remaining time by the tolerance, which covers the transport; the
    remaining time then becomes 0 before the increment is added.
    """

    def __init__(self, settings: MatchSettings) -> None:
        self._remaining_ms = [settings.initial_time_ms, settings.initial_time_ms]
        self._increment_ms = settings.increment_ms
        self._tolerance_ms = settings.tolerance_ms
        self._running = settings.clock

    @property
    def running(self) -> bool:
        """False if the clock is switched off: no deadlines, no time is deducted."""
        return self._running

    def remaining_ms(self, color: int) -> int:
        return self._remaining_ms[color]

    def deadline_ns(self, color: int, start_ns: int) -> int | None:
        """The latest moment for the answer to a turn sent at start_ns."""
        if not self._running:
            return None
        return start_ns + (self._remaining_ms[color] + self._tolerance_ms) * NANOSECONDS_PER_MS

    def is_over(self, color: int, elapsed_ms: int) -> bool:
        """The turn took longer than the remaining time plus the tolerance."""
        return self._running and elapsed_ms > self._remaining_ms[color] + self._tolerance_ms

    def charge(self, color: int, elapsed_ms: int) -> None:
        """Deducts a completed turn within the time and adds the increment."""
        if not self._running:
            return
        if self.is_over(color, elapsed_ms):
            raise ValueError(f"a turn of {elapsed_ms} ms is over the time; score a timeout")
        remaining = max(self._remaining_ms[color] - elapsed_ms, 0)
        self._remaining_ms[color] = remaining + self._increment_ms

    def flag(self, color: int) -> None:
        """The side ran out of time."""
        self._remaining_ms[color] = 0


def elapsed_ms(start_ns: int, end_ns: int) -> int:
    """Whole milliseconds between two monotonic times, rounded down."""
    return (end_ns - start_ns) // NANOSECONDS_PER_MS
