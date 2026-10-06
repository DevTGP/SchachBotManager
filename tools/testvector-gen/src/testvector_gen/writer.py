"""JSON layout of a vector file: readable top level, one compact line per vector, LF endings."""

import json


def _dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(", ", ": "))


def render(schema: str, description: str, vectors: list[dict]) -> str:
    lines = [
        "{",
        f'  "$schema": {_dumps(schema)},',
        f'  "description": {_dumps(description)},',
        '  "vectors": [',
    ]
    lines += [
        f"    {_dumps(vector)}{',' if index < len(vectors) - 1 else ''}"
        for index, vector in enumerate(vectors)
    ]
    lines += ["  ]", "}"]
    return "\n".join(lines) + "\n"
