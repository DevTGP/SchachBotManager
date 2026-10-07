"""Runs all checks on a spec directory."""

from pathlib import Path

from spec_check.api import check_api
from spec_check.documents import check_documents
from spec_check.examples import check_examples
from spec_check.loading import load_json_files
from spec_check.openapi import check_openapi, is_openapi_document
from spec_check.patterns import check_patterns
from spec_check.problem import Problem
from spec_check.schemas import build_registry, check_schemas
from spec_check.testvectors import check_testvectors


def check_spec(root: Path) -> list[Problem]:
    """Expects an absolute, normalized root directory."""
    documents, problems = load_json_files(root)
    schema_problems, valid_schemas = check_schemas(documents)
    problems.extend(schema_problems)
    schemas = {path: documents[path] for path in valid_schemas}
    openapi = {path: doc for path, doc in documents.items() if is_openapi_document(doc)}
    problems.extend(check_patterns(schemas | openapi))
    registry = build_registry(schemas)
    problems.extend(check_documents(documents, registry, valid_schemas))
    problems.extend(check_examples(documents, registry, valid_schemas, root))
    problems.extend(check_api(documents, registry, valid_schemas, root))
    problems.extend(check_testvectors(documents, registry, valid_schemas, root))
    problems.extend(check_openapi(openapi))
    return problems
