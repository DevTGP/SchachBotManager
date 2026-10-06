import json
from pathlib import Path

import pytest

from spec_check.check import check_spec

REPO_API_SCHEMA = Path(__file__).resolve().parents[3] / "spec" / "api" / "api.schema.json"


def api_file(module: str, **sections: object) -> dict:
    return {"$schema": "api.schema.json", "module": module, "description": "x", **sections}


@pytest.fixture
def api(spec_root: Path, write_json):
    """Writes the real API schema and a small, consistent API; returns a writer for more files."""
    write_json("api/api.schema.json", json.loads(REPO_API_SCHEMA.read_text(encoding="utf-8")))
    write_json(
        "api/primitives.json",
        api_file(
            "primitives",
            primitives=[
                {
                    "name": "u8",
                    "description": "x",
                    "languages": dict.fromkeys(
                        ["python", "cpp", "java", "csharp", "javascript"], "int"
                    ),
                }
            ],
        ),
    )
    write_json(
        "api/types.json",
        api_file(
            "types",
            types=[
                {"name": "Color", "kind": "alias", "base": "u8", "description": "x"},
                {"name": "Board", "kind": "class", "description": "x"},
                {
                    "name": "Info",
                    "kind": "record",
                    "description": "x",
                    "fields": [{"name": "depth", "type": "u8", "description": "x"}],
                },
            ],
        ),
    )
    write_json("api/errors.json", api_file("errors", errors=[{"name": "Bad", "description": "x"}]))

    def write(module: str, **sections: object) -> Path:
        return write_json(f"api/{module}.json", api_file(module, **sections))

    return write


def method(name: str, owner: str = "Board", **extra: object) -> dict:
    return {
        "name": name,
        "kind": "method",
        "owner": owner,
        "params": [],
        "description": "x",
        **extra,
    }


def messages(spec_root: Path) -> list[str]:
    return [problem.message for problem in check_spec(spec_root)]


def test_consistent_api_passes(spec_root: Path, api):
    api(
        "board",
        functions=[method("side_to_move", returns={"type": "Color"}, errors=["Bad"])],
    )
    api("constants", constants=[{"name": "BLACK", "type": "Color", "value": 1}])

    assert messages(spec_root) == []


def test_reports_unknown_type_inside_list(spec_root: Path, api):
    api("board", functions=[method("moves", returns={"type": "list<Move>"})])

    assert messages(spec_root) == ["unknown type: list<Move>"]


def test_reports_unknown_error(spec_root: Path, api):
    api("board", functions=[method("fen", errors=["Missing"])])

    assert messages(spec_root) == ["unknown error: Missing"]


def test_reports_owner_that_is_a_record(spec_root: Path, api):
    api("info", functions=[method("clear", owner="Info")])

    assert messages(spec_root) == ["owner is no class or value type: Info"]


def test_reports_duplicate_function_of_one_owner(spec_root: Path, api):
    api("board", functions=[method("fen")])
    api("board_more", functions=[method("fen")])

    assert messages(spec_root) == ["duplicate name: Board.fen"]


def test_reports_duplicate_constant_across_files(spec_root: Path, api):
    api("constants", constants=[{"name": "WHITE", "type": "Color", "value": 0}])
    api("more_constants", constants=[{"name": "WHITE", "type": "Color", "value": 0}])

    assert messages(spec_root) == ["duplicate name: WHITE"]


def test_reports_constant_out_of_range(spec_root: Path, api):
    api("constants", constants=[{"name": "BIG", "type": "Color", "value": 256}])

    assert messages(spec_root) == ["value of BIG out of range for Color"]


def test_reports_constant_of_unknown_type(spec_root: Path, api):
    api("constants", constants=[{"name": "X", "type": "Square", "value": 1}])

    assert messages(spec_root) == ["unknown type of X: Square"]


def test_reports_module_not_named_after_file(spec_root: Path, api, write_json):
    write_json("api/board.json", api_file("other", functions=[method("fen")]))

    assert messages(spec_root) == ["module must be named after its file: board"]


def test_reports_api_file_without_api_schema(spec_root: Path, api, write_json):
    write_json("api/notes.json", {"text": "x"})

    assert messages(spec_root) == ["API files must name api.schema.json as $schema"]


def test_file_violating_the_schema_is_not_cross_checked(spec_root: Path, api):
    api("board", functions=[method("fen", returns={"type": "Missing"}, extra=1)])

    problems = messages(spec_root)

    assert len(problems) == 1
    assert "extra" in problems[0]
