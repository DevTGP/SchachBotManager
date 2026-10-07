"""Parsing of JSON request bodies; invalid values become invalid_parameter errors."""

from collections.abc import Collection
from typing import Any

from bson import ObjectId
from flask import request

from sbm_api.errors import invalid_parameter
from sbm_api.params import object_id

MISSING: Any = object()


def json_object(allowed: Collection[str]) -> dict:
    """The body as an object with no other fields than allowed."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise invalid_parameter("body", "the body must be a JSON object")
    for field in data:
        if field not in allowed:
            raise invalid_parameter(field, f"unknown field {field}")
    return data


def string(data: dict, field: str, *, max_length: int, default: Any = MISSING) -> str:
    value = _value(data, field, default)
    if value is default and default is not MISSING:
        return value
    if not isinstance(value, str) or not 1 <= len(value) <= max_length:
        raise invalid_parameter(field, f"{field} must be a text of 1 to {max_length} characters")
    return value


def boolean(data: dict, field: str, *, default: Any = MISSING) -> bool:
    value = _value(data, field, default)
    if not isinstance(value, bool):
        raise invalid_parameter(field, f"{field} must be true or false")
    return value


def integer(data: dict, field: str, *, low: int, high: int, default: Any = MISSING) -> int:
    value = _value(data, field, default)
    # bool is an int in Python but not in JSON.
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise invalid_parameter(field, f"{field} must be an integer from {low} to {high}")
    return value


def choice(data: dict, field: str, choices: Collection[str]) -> str:
    value = _value(data, field, MISSING)
    if value not in choices:
        raise invalid_parameter(field, f"{field} must be one of {', '.join(choices)}")
    return value


def identifier(data: dict, field: str) -> ObjectId:
    value = _value(data, field, MISSING)
    if not isinstance(value, str):
        raise invalid_parameter(field, f"{field} must be 24 lowercase hexadecimal digits")
    return object_id(value, field)


def _value(data: dict, field: str, default: Any) -> Any:
    if field in data:
        return data[field]
    if default is MISSING:
        raise invalid_parameter(field, f"{field} is required")
    return default
