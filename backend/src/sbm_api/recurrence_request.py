"""The calendar in the bodies of leagues and tournaments (schema Recurrence, E171)."""

import re
from datetime import UTC, datetime

from sbm_store import recurrence

from sbm_api.errors import invalid_parameter
from sbm_api.timestamps import timestamp

# RFC 3339 with a time zone; fromisoformat alone also takes forms without one.
RFC3339 = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?(Z|[+-][0-9]{2}:[0-9]{2})"
)
MESSAGE = (
    "recurrence must be null or have first_start (RFC 3339) and interval_hours "
    f"from {recurrence.MIN_HOURS} to {recurrence.MAX_HOURS}"
)


def parse(value) -> dict | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {"first_start", "interval_hours"}:
        raise invalid_parameter("recurrence", MESSAGE)
    first_start, hours = value["first_start"], value["interval_hours"]
    if not isinstance(first_start, str) or RFC3339.fullmatch(first_start) is None:
        raise invalid_parameter("recurrence", MESSAGE)
    if isinstance(hours, bool) or not isinstance(hours, int):
        raise invalid_parameter("recurrence", MESSAGE)
    if not recurrence.MIN_HOURS <= hours <= recurrence.MAX_HOURS:
        raise invalid_parameter("recurrence", MESSAGE)
    try:
        start = datetime.fromisoformat(first_start.replace("Z", "+00:00"))
    except ValueError:
        raise invalid_parameter("recurrence", MESSAGE) from None
    # MongoDB keeps milliseconds; the stored date is the one the API shows.
    start = start.astimezone(UTC).replace(microsecond=start.microsecond // 1000 * 1000)
    return recurrence.new_recurrence(start, hours)


def view(value: dict | None) -> dict | None:
    if value is None:
        return None
    return {
        "first_start": timestamp(value["first_start"]),
        "interval_hours": value["interval_hours"],
    }
