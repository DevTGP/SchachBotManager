"""The bodies of POST and PATCH /admin/disciplines (E100), and disciplines chosen for matches."""

import re

from pymongo.database import Database
from sbm_store import disciplines
from sbm_store.discipline import (
    DEFAULT_MAX_MOVES,
    DEFAULT_STARTUP_MS,
    DEFAULT_TOLERANCE_MS,
    Discipline,
)

from sbm_api import body
from sbm_api.errors import invalid_parameter

MAX_NAME = 40
CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")
# The ranges of the settings an admin may give, as in the schema DisciplineRequest.
LIMITS = {
    "initial_time_ms": (1000, 86_400_000),
    "increment_ms": (0, 3_600_000),
    "startup_ms": (1000, 60_000),
    "tolerance_ms": (0, 1000),
    "max_moves": (1, 2000),
}
DEFAULTS = {
    "increment_ms": 0,
    "startup_ms": DEFAULT_STARTUP_MS,
    "tolerance_ms": DEFAULT_TOLERANCE_MS,
    "max_moves": DEFAULT_MAX_MOVES,
}


def parse_new() -> Discipline:
    data = body.json_object(("name", *LIMITS))
    settings = {
        field: body.integer(
            data, field, low=low, high=high, default=DEFAULTS.get(field, body.MISSING)
        )
        for field, (low, high) in LIMITS.items()
    }
    return Discipline(name=name(data), **settings)


def parse_update() -> dict:
    """The fields to change; at least one."""
    data = body.json_object(("name", *LIMITS, "archived"))
    if not data:
        raise invalid_parameter("body", "change at least one field")
    fields = {}
    if "name" in data:
        fields["name"] = name(data)
    for field, (low, high) in LIMITS.items():
        if field in data:
            fields[field] = body.integer(data, field, low=low, high=high)
    if "archived" in data:
        fields["archived"] = body.boolean(data, "archived")
    return fields


def name(data: dict) -> str:
    value = data.get("name")
    if isinstance(value, str):
        value = value.strip()
    if not isinstance(value, str) or not 1 <= len(value) <= MAX_NAME or CONTROL.search(value):
        raise invalid_parameter(
            "name", f"name must be 1 to {MAX_NAME} characters, no control characters"
        )
    return value


def chosen(db: Database, data: dict) -> Discipline | None:
    """The discipline a match request names in discipline_id; None for free times."""
    if data.get("discipline_id") is None:
        return None
    discipline = disciplines.get(db, body.identifier(data, "discipline_id"))
    if discipline is None or discipline["archived"]:
        raise invalid_parameter("discipline_id", "discipline_id is not a discipline in use")
    for field in ("initial_time_ms", "increment_ms", "max_moves"):
        if field in data:
            raise invalid_parameter(field, f"{field} is part of the discipline")
    return disciplines.snapshot(discipline)
