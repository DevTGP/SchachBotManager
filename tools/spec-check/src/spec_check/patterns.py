"""Checks that regular expressions in schemas behave the same in all SDK languages.

Python's `\\d` also matches non-ASCII digits, and its `$` also matches before a trailing
newline. ECMA-262, Java and .NET differ, so schemas use `[0-9]` and end with `(?!\\n)$`.
"""

from collections.abc import Iterator
from pathlib import Path

from spec_check.problem import Problem

PORTABLE_END = "(?!\\n)$"


def find_patterns(node: object) -> Iterator[str]:
    """Yields every string value of a `pattern` keyword in a schema."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "pattern" and isinstance(value, str):
                yield value
            else:
                yield from find_patterns(value)
    elif isinstance(node, list):
        for item in node:
            yield from find_patterns(item)


def pattern_problems(pattern: str) -> list[str]:
    problems = []
    if "\\d" in pattern:
        problems.append(f"use [0-9] instead of \\d: {pattern}")
    if pattern.endswith("$") and not pattern.endswith(PORTABLE_END):
        problems.append(f"end with {PORTABLE_END} instead of $: {pattern}")
    return problems


def check_patterns(schemas: dict[Path, object]) -> list[Problem]:
    return [
        Problem(path, message)
        for path, schema in schemas.items()
        for pattern in find_patterns(schema)
        for message in pattern_problems(pattern)
    ]
