"""Runs all checks on a spec directory."""

from pathlib import Path

from spec_check.documents import check_documents
from spec_check.examples import check_examples
from spec_check.loading import load_json_files
from spec_check.patterns import check_patterns
from spec_check.problem import Problem
from spec_check.schemas import build_registry, check_schemas


def check_spec(root: Path) -> list[Problem]:
    """Expects an absolute, normalized root directory."""
    documents, problems = load_json_files(root)
    schema_problems, valid_schemas = check_schemas(documents)
    problems.extend(schema_problems)
    schemas = {path: documents[path] for path in valid_schemas}
    problems.extend(check_patterns(schemas))
    registry = build_registry(schemas)
    problems.extend(check_documents(documents, registry, valid_schemas))
    problems.extend(check_examples(documents, registry, valid_schemas, root))
    return problems
