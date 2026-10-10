"""Parsing of path and query parameters; invalid values become invalid_parameter errors."""

import re
from collections.abc import Collection, Mapping
from datetime import date

from bson import ObjectId

from sbm_api.errors import invalid_parameter

# Lowercase only, as in the Id schema; ObjectId itself would also take uppercase.
OBJECT_ID = re.compile(r"[0-9a-f]{24}")
INTEGER = re.compile(r"-?[0-9]{1,9}")
# fromisoformat alone also takes forms such as 20261010.
DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def object_id(value: str, field: str) -> ObjectId:
    if OBJECT_ID.fullmatch(value) is None:
        raise invalid_parameter(field, f"{field} must be 24 lowercase hexadecimal digits")
    return ObjectId(value)


def optional_object_id(args: Mapping[str, str], field: str) -> ObjectId | None:
    value = args.get(field)
    return None if value is None else object_id(value, field)


def optional_choice(args: Mapping[str, str], field: str, choices: Collection[str]) -> str | None:
    value = args.get(field)
    if value is not None and value not in choices:
        raise invalid_parameter(field, f"{field} must be one of {', '.join(choices)}")
    return value


def integer(args: Mapping[str, str], field: str, *, default: int, low: int, high: int) -> int:
    value = args.get(field)
    if value is None:
        return default
    if INTEGER.fullmatch(value) is None or not low <= int(value) <= high:
        raise invalid_parameter(field, f"{field} must be an integer from {low} to {high}")
    return int(value)


def optional_date(args: Mapping[str, str], field: str) -> date | None:
    value = args.get(field)
    if value is None:
        return None
    try:
        if DATE.fullmatch(value) is not None:
            return date.fromisoformat(value)
    except ValueError:
        pass
    raise invalid_parameter(field, f"{field} must be a date such as 2026-10-10")
