"""Discovery and parsing of all JSON files below the spec root."""

import json
from pathlib import Path

from spec_check.problem import Problem


def load_json_files(root: Path) -> tuple[dict[Path, object], list[Problem]]:
    documents: dict[Path, object] = {}
    problems: list[Problem] = []
    for path in sorted(root.rglob("*.json")):
        try:
            documents[path] = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            problems.append(Problem(path, f"invalid JSON: {exc}"))
    return documents, problems
