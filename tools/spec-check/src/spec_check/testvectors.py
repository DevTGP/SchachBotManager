"""Checks the test vectors below testvectors/ against the canonical bot API below api/.

The schemas check each vector file on its own. This check resolves every call vector against the
API: the function must be a Board or Move function, receiver and arguments must match its
parameters, the result its return type and the error one of its declared errors. Ids are unique
across all vector files and start with the path of their file. Every Board and Move function
needs a vector that succeeds and one for each declared error (E55).
"""

import os
from pathlib import Path

from referencing import Registry

from spec_check.api import api_documents, entries, primitive_of
from spec_check.problem import Problem
from spec_check.schemas import is_schema_file, validate_against
from spec_check.vector_values import MOVE, fits

VECTORS_DIR = "testvectors"
CALLS_SCHEMA = "calls.schema.json"
PERFT_SCHEMA = "perft.schema.json"
RECEIVERS = {"Board": "board", "Move": "move"}
CALLABLE_KINDS = ("constructor", "static", "method")
RESULT_KEYS = ("result", "result_contains")

Function = tuple[Path, dict]


def vector_documents(
    documents: dict[Path, object], registry: Registry, valid_schemas: set[Path], root: Path
) -> tuple[dict[Path, tuple[str, dict]], list[Problem]]:
    """Vector files that pass their schema, with the schema name, and problems for files that
    name neither vector schema. Schema violations are reported by the document check."""
    directory = root / VECTORS_DIR
    valid: dict[Path, tuple[str, dict]] = {}
    problems: list[Problem] = []
    for path, document in documents.items():
        if path.relative_to(root).parts[0] != VECTORS_DIR or is_schema_file(path):
            continue
        reference = document.get("$schema") if isinstance(document, dict) else None
        schema_path = (
            Path(os.path.normpath(path.parent / reference)) if isinstance(reference, str) else None
        )
        if schema_path not in (directory / CALLS_SCHEMA, directory / PERFT_SCHEMA):
            message = f"vector files must name {CALLS_SCHEMA} or {PERFT_SCHEMA}"
            problems.append(Problem(path, message))
        elif schema_path in valid_schemas and not validate_against(registry, schema_path, document):
            valid[path] = (schema_path.name, document)
    return valid, problems


def tested_functions(api: dict[Path, dict]) -> dict[str, Function]:
    return {
        f"{item['owner']}.{item['name']}": (path, item)
        for path, item in entries(api, "functions")
        if item.get("owner") in RECEIVERS and item["kind"] in CALLABLE_KINDS
    }


def id_prefix(path: Path, root: Path) -> str:
    return ".".join(path.relative_to(root / VECTORS_DIR).with_suffix("").parts) + "."


def check_call(vector: dict, function: dict, types: dict[str, dict]) -> list[str]:
    """Messages for a call vector of a known function."""
    messages = []
    owner, kind = function["owner"], function["kind"]
    receiver = RECEIVERS[owner] if kind == "method" else None
    for field in RECEIVERS.values():
        if field == receiver and field not in vector:
            messages.append(f"{field} missing for a method of {owner}")
        elif field != receiver and field in vector:
            messages.append(f"{field} not allowed for this function")
    if "move" in vector and not fits(vector["move"], MOVE, types):
        messages.append("move is no valid Move")

    params = function.get("params", [])
    if len(vector["args"]) != len(params):
        messages.append(f"{len(params)} argument(s) expected, {len(vector['args'])} given")
    else:
        messages.extend(
            f"argument {param['name']} does not fit {param['type']}"
            for value, param in zip(vector["args"], params, strict=True)
            if not fits(value, param["type"], types)
        )

    returns = function.get("returns", {}).get("type")
    if "result" in vector:
        result = vector["result"]
        if not (result is None if returns is None else fits(result, returns, types)):
            messages.append(f"result does not fit {returns or 'no return value'}")
        if "unordered" in vector and not isinstance(result, list):
            messages.append("unordered requires a list result")
    if "result_contains" in vector and primitive_of(returns, types) != "string":
        messages.append("result_contains requires a string result")
    if "error" in vector and vector["error"] not in function.get("errors", []):
        messages.append(f"error not declared for the function: {vector['error']}")
    return messages


def check_testvectors(
    documents: dict[Path, object], registry: Registry, valid_schemas: set[Path], root: Path
) -> list[Problem]:
    if not (root / VECTORS_DIR).is_dir():
        return []
    files, problems = vector_documents(documents, registry, valid_schemas, root)
    api, _ = api_documents(documents, registry, valid_schemas, root)
    types = {item["name"]: item for _, item in entries(api, "types")}
    functions = tested_functions(api)

    seen_ids: set[str] = set()
    succeeding: set[str] = set()
    failing: set[tuple[str, str]] = set()
    for path, (schema, document) in files.items():
        prefix = id_prefix(path, root)
        for vector in document["vectors"]:
            vector_id = vector["id"]
            if vector_id in seen_ids:
                problems.append(Problem(path, f"duplicate id: {vector_id}"))
            seen_ids.add(vector_id)
            if not vector_id.startswith(prefix):
                problems.append(Problem(path, f"{vector_id}: id must start with {prefix}"))
            if schema != CALLS_SCHEMA:
                continue
            name = vector["function"]
            if name not in functions:
                problems.append(Problem(path, f"{vector_id}: no Board or Move function: {name}"))
                continue
            problems.extend(
                Problem(path, f"{vector_id}: {message}")
                for message in check_call(vector, functions[name][1], types)
            )
            if "error" in vector:
                failing.add((name, vector["error"]))
            else:
                succeeding.add(name)

    for name, (path, function) in functions.items():
        if name not in succeeding:
            problems.append(Problem(path, f"no succeeding test vector for {name}"))
        problems.extend(
            Problem(path, f"no test vector for {name} raising {error}")
            for error in function.get("errors", [])
            if (name, error) not in failing
        )
    return problems
