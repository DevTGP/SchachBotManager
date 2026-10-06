"""Checks cross references between the files of the canonical bot API below api/.

Every API file must follow api/api.schema.json, which checks each file on its own. This check
resolves names across the files that pass it: every referenced type, owner and error must be
declared, names must be unique, each module is named after its file, and constant values must
fit the primitive behind their type.
"""

import re
from collections.abc import Callable, Iterator
from pathlib import Path

from referencing import Registry

from spec_check.problem import Problem
from spec_check.schemas import is_schema_file, validate_against

API_DIR = "api"
API_SCHEMA = "api.schema.json"
LIST_TYPE = re.compile(r"^list<(.+)>$")
OWNER_KINDS = ("class", "value")
RANGES = {
    "u8": (0, 2**8 - 1),
    "u16": (0, 2**16 - 1),
    "i32": (-(2**31), 2**31 - 1),
    "i64": (-(2**63), 2**63 - 1),
    "u64": (0, 2**64 - 1),
}

Entry = tuple[Path, dict]


def api_documents(
    documents: dict[Path, object], registry: Registry, valid_schemas: set[Path], root: Path
) -> tuple[dict[Path, dict], list[Problem]]:
    """Returns the API files that pass the API schema, and problems for files not naming it.

    Schema violations are reported by the document check and are not repeated here.
    """
    schema_path = root / API_DIR / API_SCHEMA
    valid: dict[Path, dict] = {}
    problems: list[Problem] = []
    for path, document in documents.items():
        if path.relative_to(root).parts[0] != API_DIR or is_schema_file(path):
            continue
        if not isinstance(document, dict) or document.get("$schema") != API_SCHEMA:
            problems.append(Problem(path, f"API files must name {API_SCHEMA} as $schema"))
        elif schema_path in valid_schemas and not validate_against(registry, schema_path, document):
            valid[path] = document
    return valid, problems


def entries(documents: dict[Path, dict], section: str) -> Iterator[Entry]:
    for path, document in documents.items():
        yield from ((path, item) for item in document.get(section, []))


def duplicates(items: list[Entry], key: Callable[[dict], str]) -> list[Problem]:
    seen: set = set()
    problems = []
    for path, item in items:
        name = key(item)
        if name in seen:
            problems.append(Problem(path, f"duplicate name: {name}"))
        seen.add(name)
    return problems


def element_type(reference: str) -> str:
    match = LIST_TYPE.match(reference)
    return match.group(1) if match else reference


def type_references(documents: dict[Path, dict]) -> Iterator[tuple[Path, str]]:
    for path, item in entries(documents, "types"):
        if "base" in item:
            yield path, item["base"]
        for field in item.get("fields", []):
            yield path, field["type"]
    for path, item in entries(documents, "functions"):
        for param in item.get("params", []):
            yield path, param["type"]
        if "returns" in item:
            yield path, item["returns"]["type"]


def primitive_of(name: str | None, types: dict[str, dict]) -> str | None:
    """Follows base types down to their primitive; None for records and classes."""
    visited = set()
    while name in types and name not in visited:
        visited.add(name)
        name = types[name].get("base")
    return name


def check_api(
    documents: dict[Path, object], registry: Registry, valid_schemas: set[Path], root: Path
) -> list[Problem]:
    api, problems = api_documents(documents, registry, valid_schemas, root)
    primitives = list(entries(api, "primitives"))
    types = list(entries(api, "types"))
    errors = list(entries(api, "errors"))
    constants = list(entries(api, "constants"))
    functions = list(entries(api, "functions"))

    problems.extend(
        Problem(path, f"module must be named after its file: {path.stem}")
        for path, document in api.items()
        if document["module"] != path.stem
    )
    for items in (primitives, types, errors, constants):
        problems.extend(duplicates(items, lambda item: item["name"]))
    problems.extend(duplicates(functions, lambda item: f"{item.get('owner', '')}.{item['name']}"))

    type_by_name = {item["name"]: item for _, item in types}
    known_types = {item["name"] for _, item in primitives} | set(type_by_name)
    error_names = {item["name"] for _, item in errors}

    for path, reference in type_references(api):
        if element_type(reference) not in known_types:
            problems.append(Problem(path, f"unknown type: {reference}"))
    for path, item in functions:
        owner = item.get("owner")
        if owner is not None and type_by_name.get(owner, {}).get("kind") not in OWNER_KINDS:
            problems.append(Problem(path, f"owner is no class or value type: {owner}"))
        for error in item.get("errors", []):
            if error not in error_names:
                problems.append(Problem(path, f"unknown error: {error}"))
    for path, item in constants:
        name, type_name, value = item["name"], item["type"], item["value"]
        if type_name not in type_by_name:
            problems.append(Problem(path, f"unknown type of {name}: {type_name}"))
            continue
        bounds = RANGES.get(primitive_of(type_name, type_by_name))
        if bounds and not bounds[0] <= value <= bounds[1]:
            problems.append(Problem(path, f"value of {name} out of range for {type_name}"))
    return problems
