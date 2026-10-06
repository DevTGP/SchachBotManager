"""Validates documents that name their schema through a relative `$schema` path."""

import os
from pathlib import Path
from urllib.parse import urlparse

from referencing import Registry

from spec_check.problem import Problem
from spec_check.schemas import validate_against


def schema_reference(document: object) -> str | None:
    """Returns the relative schema path of a document, or None if it names no local schema."""
    if not isinstance(document, dict):
        return None
    reference = document.get("$schema")
    if not isinstance(reference, str) or urlparse(reference).scheme:
        return None
    return reference


def check_documents(
    documents: dict[Path, object], registry: Registry, valid_schemas: set[Path]
) -> list[Problem]:
    problems: list[Problem] = []
    for path, document in documents.items():
        reference = schema_reference(document)
        if reference is None:
            continue
        schema_path = Path(os.path.normpath(path.parent / reference))
        if schema_path not in valid_schemas:
            problems.append(Problem(path, f"schema missing or invalid: {reference}"))
            continue
        problems.extend(
            Problem(path, message) for message in validate_against(registry, schema_path, document)
        )
    return problems
