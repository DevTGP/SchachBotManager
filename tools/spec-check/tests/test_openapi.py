from pathlib import Path

import pytest

from spec_check.check import check_spec
from spec_check.openapi import is_openapi_document


def openapi(schemas: dict, parameters: list | None = None) -> dict:
    """A one-route OpenAPI document whose response is the schema `Answer`."""
    operation = {
        "responses": {
            "200": {
                "description": "ok",
                "content": {
                    "application/json": {"schema": {"$ref": "#/components/schemas/Answer"}}
                },
            }
        }
    }
    path_item = {"get": operation}
    if parameters is not None:
        path_item["parameters"] = parameters
    return {
        "openapi": "3.1.1",
        "info": {"title": "test", "version": "1"},
        "paths": {"/answers/{answer_id}": path_item},
        "components": {"schemas": schemas},
    }


ID_PARAMETER = [{"name": "answer_id", "in": "path", "required": True, "schema": {"type": "string"}}]


def test_only_documents_with_an_openapi_field_are_openapi():
    assert is_openapi_document({"openapi": "3.1.1"})
    assert not is_openapi_document({"$schema": "x.schema.json"})
    assert not is_openapi_document([1])


def test_valid_document_with_reference_into_a_protocol_schema_passes(
    spec_root: Path, write_json, ping_schema
):
    answer = {"$ref": "../protocol/v1/ping.schema.json#/properties/type"}
    write_json("web/openapi.json", openapi({"Answer": answer}, ID_PARAMETER))

    assert check_spec(spec_root) == []


def test_unresolvable_reference_is_reported(spec_root: Path, write_json):
    answer = {"$ref": "../protocol/v1/missing.schema.json#/x"}
    doc = write_json("web/openapi.json", openapi({"Answer": answer}, ID_PARAMETER))

    problems = check_spec(spec_root)

    assert [p.path for p in problems] == [doc]
    assert "unresolvable reference" in problems[0].message


def test_undeclared_path_parameter_is_reported(spec_root: Path, write_json):
    doc = write_json("web/openapi.json", openapi({"Answer": {"type": "string"}}))

    problems = check_spec(spec_root)

    assert [p.path for p in problems] == [doc]
    assert "answer_id" in problems[0].message


def test_invalid_schema_is_reported(spec_root: Path, write_json):
    doc = write_json("web/openapi.json", openapi({"Answer": {"type": "strin"}}, ID_PARAMETER))

    assert [p.path for p in check_spec(spec_root)] == [doc]


@pytest.mark.parametrize("version", ["3.0.3", 3.1])
def test_other_versions_are_reported(spec_root: Path, write_json, version):
    document = openapi({"Answer": {"type": "string"}}, ID_PARAMETER)
    document["openapi"] = version
    doc = write_json("web/openapi.json", document)

    problems = check_spec(spec_root)

    assert [p.path for p in problems] == [doc]
    assert "unsupported OpenAPI version" in problems[0].message


def test_patterns_in_openapi_documents_are_checked(spec_root: Path, write_json):
    answer = {"type": "string", "pattern": r"^\d$"}
    doc = write_json("web/openapi.json", openapi({"Answer": answer}, ID_PARAMETER))

    problems = check_spec(spec_root)

    assert [p.path for p in problems] == [doc, doc]
