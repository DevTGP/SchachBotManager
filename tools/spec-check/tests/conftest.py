import json
from collections.abc import Callable
from pathlib import Path

import pytest

DRAFT = "https://json-schema.org/draft/2020-12/schema"

WriteJson = Callable[[str, object], Path]


@pytest.fixture
def spec_root(tmp_path: Path) -> Path:
    root = tmp_path / "spec"
    root.mkdir()
    return root.resolve()


@pytest.fixture
def write_json(spec_root: Path) -> WriteJson:
    def write(relative: str, content: object) -> Path:
        path = spec_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(content), encoding="utf-8")
        return path

    return write


@pytest.fixture
def ping_schema(write_json: WriteJson) -> Path:
    """A minimal protocol message schema with a cross-file reference."""
    write_json(
        "protocol/v1/common.schema.json",
        {"$schema": DRAFT, "$defs": {"version": {"const": 1}}},
    )
    return write_json(
        "protocol/v1/ping.schema.json",
        {
            "$schema": DRAFT,
            "type": "object",
            "properties": {
                "type": {"const": "ping"},
                "v": {"$ref": "common.schema.json#/$defs/version"},
            },
            "required": ["type", "v"],
            "additionalProperties": False,
        },
    )
