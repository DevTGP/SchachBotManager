"""The description of a bot: plain text by its owner, shown to everyone (E95)."""

import unicodedata

from sbm_api.errors import invalid_parameter

MAX_LENGTH = 500
FIELD = "description"


def check(value: object) -> str:
    """The description with line breaks as LF; browsers send form text with CR LF."""
    if not isinstance(value, str):
        raise invalid_parameter(FIELD, "description must be a text")
    text = value.replace("\r\n", "\n").replace("\r", "\n")
    if len(text) > MAX_LENGTH:
        raise invalid_parameter(FIELD, f"description must be at most {MAX_LENGTH} characters")
    if any(char != "\n" and unicodedata.category(char) == "Cc" for char in text):
        raise invalid_parameter(FIELD, "description must not hold control characters")
    return text
