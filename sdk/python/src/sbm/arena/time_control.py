"""Time controls as written on the command line and in PGN: seconds plus increment, "60+1"."""

import re
from decimal import Decimal

TIME_CONTROL = re.compile(r"(\d+(?:\.\d{1,3})?)(?:\+(\d+(?:\.\d{1,3})?))?")


class TimeControlError(ValueError):
    pass


def parse_time_control(text: str) -> tuple[int, int]:
    """Initial time and increment in milliseconds; seconds may have up to three decimals."""
    match = TIME_CONTROL.fullmatch(text.strip())
    if match is None:
        raise TimeControlError(
            f"invalid time control {text!r}, expected seconds+increment such as 60+1 or 0.5"
        )
    initial, increment = (_milliseconds(group or "0") for group in match.groups())
    if initial == 0:
        raise TimeControlError("the initial time must be more than 0 seconds")
    return initial, increment


def _milliseconds(seconds: str) -> int:
    return int(Decimal(seconds) * 1000)


def format_time_control(initial_ms: int, increment_ms: int) -> str:
    """The PGN form, e.g. 60+1 or 0.5+0; seconds without needless decimals."""
    return f"{_seconds(initial_ms)}+{_seconds(increment_ms)}"


def _seconds(milliseconds: int) -> str:
    whole, rest = divmod(milliseconds, 1000)
    return str(whole) if rest == 0 else f"{whole}.{rest:03d}".rstrip("0")
