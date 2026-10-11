"""The calendar of a league or tournament (E171): dates first_start + k · interval_hours.

A calendar is None or a document with first_start and interval_hours. Without one, a new season
or edition waits for an admin.
"""

from datetime import datetime, timedelta

MIN_HOURS = 1
MAX_HOURS = 8760


def new_recurrence(first_start: datetime, interval_hours: int) -> dict:
    return {"first_start": first_start, "interval_hours": interval_hours}


def next_slot(
    recurrence: dict | None, after: datetime, *, inclusive: bool = False
) -> datetime | None:
    """The first date after `after` (or at it, if inclusive); None without a calendar."""
    if recurrence is None:
        return None
    first = recurrence["first_start"]
    if after < first:
        return first
    step = timedelta(hours=recurrence["interval_hours"])
    slot = first + (after - first) // step * step
    if inclusive and slot == after:
        return slot
    return slot + step
