"""Validates OpenAPI documents, the web API contract below spec/web/ (E73).

A document is an OpenAPI document if its top level has an `openapi` field. Relative `$ref`s,
such as those into the protocol schemas, resolve against the document's file location.
"""

from pathlib import Path

from openapi_spec_validator.validation.validators import OpenAPIV31SpecValidator
from referencing.exceptions import Unresolvable

from spec_check.problem import Problem

SUPPORTED_PREFIX = "3.1."


def is_openapi_document(document: object) -> bool:
    return isinstance(document, dict) and "openapi" in document


def check_openapi(documents: dict[Path, object]) -> list[Problem]:
    problems: list[Problem] = []
    for path, document in documents.items():
        if is_openapi_document(document):
            problems.extend(Problem(path, message) for message in _validate(path, document))
    return problems


def _validate(path: Path, document: dict) -> list[str]:
    version = document["openapi"]
    if not isinstance(version, str) or not version.startswith(SUPPORTED_PREFIX):
        return [f"unsupported OpenAPI version {version!r}, expected 3.1.x"]
    validator = OpenAPIV31SpecValidator(document, base_uri=path.as_uri())
    try:
        return [error.message for error in validator.iter_errors()]
    except Unresolvable as exc:
        return [f"unresolvable reference: {exc.ref}"]
