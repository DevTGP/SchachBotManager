"""Checks protocol example messages against the schema of their message type.

Layout: protocol/v<N>/examples/{valid,invalid}/<type>.<case>.json, validated against
protocol/v<N>/<type>.schema.json. Valid examples must pass, invalid ones must fail.
"""

from pathlib import Path

from referencing import Registry

from spec_check.problem import Problem
from spec_check.schemas import SCHEMA_SUFFIX, validate_against

EXPECTATIONS = ("valid", "invalid")


def is_example(relative: Path) -> bool:
    parts = relative.parts
    return len(parts) >= 3 and parts[0] == "protocol" and parts[2] == "examples"


def example_schema_path(path: Path) -> Path:
    message_type = path.name.split(".", 1)[0]
    return path.parent.parent.parent / f"{message_type}{SCHEMA_SUFFIX}"


def check_examples(
    documents: dict[Path, object], registry: Registry, valid_schemas: set[Path], root: Path
) -> list[Problem]:
    problems: list[Problem] = []
    for path, document in documents.items():
        relative = path.relative_to(root)
        if not is_example(relative):
            continue
        if len(relative.parts) != 5 or relative.parts[3] not in EXPECTATIONS:
            problems.append(Problem(path, "examples belong in examples/valid or examples/invalid"))
            continue
        schema_path = example_schema_path(path)
        if schema_path not in valid_schemas:
            problems.append(Problem(path, f"schema missing or invalid: {schema_path.name}"))
            continue
        violations = validate_against(registry, schema_path, document)
        if relative.parts[3] == "valid":
            problems.extend(Problem(path, message) for message in violations)
        elif not violations:
            problems.append(Problem(path, "invalid example passes its schema"))
    return problems
