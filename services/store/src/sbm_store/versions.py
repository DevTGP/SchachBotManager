"""Version numbers of bots as their owners give them: X.Y.Z, each part 0 to 999 (E91)."""

import re

FIRST = "1.0.0"
_VERSION = re.compile(r"(0|[1-9]\d{0,2})\.(0|[1-9]\d{0,2})\.(0|[1-9]\d{0,2})")


def parse(text: str) -> tuple[int, int, int] | None:
    """The parts of a version for comparing, None if text is no version."""
    match = _VERSION.fullmatch(text)
    if match is None:
        return None
    major, minor, patch = (int(part) for part in match.groups())
    return major, minor, patch


def next_patch(text: str) -> str | None:
    """The version after text with the last part raised; None at 999 or for no version."""
    parts = parse(text)
    if parts is None or parts[2] == 999:
        return None
    major, minor, patch = parts
    return f"{major}.{minor}.{patch + 1}"
