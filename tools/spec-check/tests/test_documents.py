from pathlib import Path

from conftest import DRAFT

from spec_check.check import check_spec
from spec_check.documents import schema_reference

VECTOR_SCHEMA = {
    "$schema": DRAFT,
    "type": "object",
    "properties": {"$schema": {"type": "string"}, "vectors": {"type": "array"}},
    "required": ["vectors"],
}


def test_schema_reference_only_for_relative_paths():
    assert schema_reference({"$schema": "schema/x.schema.json"}) == "schema/x.schema.json"
    assert schema_reference({"$schema": DRAFT}) is None
    assert schema_reference({"other": 1}) is None
    assert schema_reference([1, 2]) is None


def test_document_matching_its_schema_passes(spec_root: Path, write_json):
    write_json("testvectors/schema/vectors.schema.json", VECTOR_SCHEMA)
    write_json(
        "testvectors/perft.json",
        {"$schema": "schema/vectors.schema.json", "vectors": []},
    )

    assert check_spec(spec_root) == []


def test_document_violating_its_schema_is_reported(spec_root: Path, write_json):
    write_json("testvectors/schema/vectors.schema.json", VECTOR_SCHEMA)
    doc = write_json("testvectors/perft.json", {"$schema": "schema/vectors.schema.json"})

    problems = check_spec(spec_root)

    assert [p.path for p in problems] == [doc]
    assert "vectors" in problems[0].message


def test_missing_schema_is_reported(spec_root: Path, write_json):
    doc = write_json("testvectors/perft.json", {"$schema": "../nowhere.schema.json"})

    problems = check_spec(spec_root)

    assert [p.path for p in problems] == [doc]
    assert "schema missing or invalid" in problems[0].message
