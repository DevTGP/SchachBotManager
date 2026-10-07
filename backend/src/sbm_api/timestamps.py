"""Times in responses: RFC 3339 in UTC with milliseconds, the precision MongoDB stores."""

from datetime import UTC, datetime


def timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def optional_timestamp(value: datetime | None) -> str | None:
    return None if value is None else timestamp(value)
