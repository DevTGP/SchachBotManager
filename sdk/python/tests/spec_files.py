"""Reads the specification below spec/ that the tests compare the binding with."""

import json
from pathlib import Path

SPEC = Path(__file__).resolve().parents[3] / "spec"

# Call vectors (spec/testvectors/calls.schema.json); perft.json has its own format.
CALL_VECTOR_FILES = sorted(
    path
    for path in (SPEC / "testvectors").rglob("*.json")
    if not path.name.endswith(".schema.json") and path.name != "perft.json"
)

# Modules of spec/api/ whose functions the native module implements.
CORE_MODULES = ["board", "board_moves", "board_query", "board_raw", "board_state", "move"]


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def core_functions() -> dict[str, dict]:
    """Board and Move functions by their full name, e.g. Board.make_move."""
    functions = {}
    for module in CORE_MODULES:
        for function in load(SPEC / "api" / f"{module}.json")["functions"]:
            functions[f"{function['owner']}.{function['name']}"] = function
    return functions


def call_vectors() -> list[dict]:
    return [vector for path in CALL_VECTOR_FILES for vector in load(path)["vectors"]]


def constants() -> list[dict]:
    return load(SPEC / "api" / "constants.json")["constants"]
