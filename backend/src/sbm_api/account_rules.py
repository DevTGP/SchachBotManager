"""Rules for names, passwords and one-time tokens in request bodies (E83, E84)."""

import re

from sbm_api import body
from sbm_api.errors import invalid_parameter

USERNAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,31}")
PASSWORD_MIN = 10
PASSWORD_MAX = 128
TOKEN = re.compile(r"[A-Za-z0-9_-]{43}")


def username(data: dict) -> str:
    value = body.string(data, "username", max_length=32)
    if USERNAME.fullmatch(value) is None:
        raise invalid_parameter(
            "username",
            "username must be 3 to 32 letters, digits, _ . or -, starting with a letter or digit",
        )
    return value


def new_password(data: dict, field: str) -> str:
    value = body.string(data, field, max_length=PASSWORD_MAX)
    if len(value) < PASSWORD_MIN:
        raise invalid_parameter(field, f"{field} must have at least {PASSWORD_MIN} characters")
    return value


def token(data: dict) -> str:
    value = body.string(data, "token", max_length=64)
    if TOKEN.fullmatch(value) is None:
        raise invalid_parameter("token", "token is not a valid link")
    return value
