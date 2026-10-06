from pathlib import Path

from conftest import DRAFT

from spec_check.schemas import build_registry, check_schemas, validate_against


def test_accepts_valid_schema_and_ignores_other_files(write_json):
    schema = write_json("a.schema.json", {"$schema": DRAFT, "type": "object"})
    other = write_json("data.json", {"type": 5})

    problems, valid = check_schemas({schema: {"type": "object"}, other: {"type": 5}})

    assert problems == []
    assert valid == {schema}


def test_reports_invalid_schema(write_json):
    schema = write_json("bad.schema.json", {"type": 5})

    problems, valid = check_schemas({schema: {"type": 5}})

    assert valid == set()
    assert [p.path for p in problems] == [schema]


def test_resolves_relative_references_between_files(ping_schema: Path):
    common = ping_schema.parent / "common.schema.json"
    registry = build_registry(
        {
            common: {"$schema": DRAFT, "$defs": {"version": {"const": 1}}},
            ping_schema: {
                "$schema": DRAFT,
                "properties": {"v": {"$ref": "common.schema.json#/$defs/version"}},
            },
        }
    )

    assert validate_against(registry, ping_schema, {"v": 1}) == []
    assert len(validate_against(registry, ping_schema, {"v": 2})) == 1


def test_reports_unresolvable_reference(write_json):
    schema = write_json("x.schema.json", {"$ref": "missing.schema.json"})
    registry = build_registry({schema: {"$ref": "missing.schema.json"}})

    messages = validate_against(registry, schema, {})

    assert len(messages) == 1
    assert "unresolvable" in messages[0]
