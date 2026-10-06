"""Checks schema files and validates instances against them.

Spec schemas carry no `$id`. Each one is registered under its file URI, so relative
`$ref`s between schema files resolve against the referring file's location.
"""

from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable
from referencing.jsonschema import DRAFT202012

from spec_check.problem import Problem

SCHEMA_SUFFIX = ".schema.json"


def is_schema_file(path: Path) -> bool:
    return path.name.endswith(SCHEMA_SUFFIX)


def check_schemas(documents: dict[Path, object]) -> tuple[list[Problem], set[Path]]:
    """Returns the problems found and the set of schema files that are valid."""
    problems: list[Problem] = []
    valid: set[Path] = set()
    for path, document in documents.items():
        if not is_schema_file(path):
            continue
        try:
            Draft202012Validator.check_schema(document)
        except SchemaError as exc:
            problems.append(Problem(path, f"invalid schema: {exc.message}"))
        else:
            valid.add(path)
    return problems, valid


def build_registry(schemas: dict[Path, object]) -> Registry:
    resources = [
        (path.as_uri(), Resource.from_contents(schema, default_specification=DRAFT202012))
        for path, schema in schemas.items()
    ]
    return Registry().with_resources(resources)


def validate_against(registry: Registry, schema_path: Path, instance: object) -> list[str]:
    """Returns one message per violation; an empty list means the instance is valid."""
    validator = Draft202012Validator({"$ref": schema_path.as_uri()}, registry=registry)
    try:
        return [
            f"{_location(error.absolute_path)}: {error.message}"
            for error in validator.iter_errors(instance)
        ]
    except Unresolvable as exc:
        return [f"unresolvable reference in {schema_path.name}: {exc}"]


def _location(path) -> str:
    return "/" + "/".join(str(part) for part in path)
