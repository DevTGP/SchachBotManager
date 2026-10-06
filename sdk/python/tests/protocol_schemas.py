"""Validates messages against the protocol schemas under spec/protocol/v1/."""

import json
from functools import cache
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012
from spec_files import SPEC

PROTOCOL = SPEC / "protocol" / "v1"


@cache
def _registry() -> Registry:
    # Schemas carry no $id; registering them under their file URI resolves relative $refs.
    resources = [
        (path.as_uri(), Resource.from_contents(json.loads(path.read_text("utf-8")), DRAFT202012))
        for path in PROTOCOL.glob("*.schema.json")
    ]
    return Registry().with_resources(resources)


def violations(schema: str, message: object) -> list[str]:
    """Messages of all violations of e.g. schema "bot_message"; empty if valid."""
    uri = (PROTOCOL / f"{schema}.schema.json").as_uri()
    validator = Draft202012Validator({"$ref": uri}, registry=_registry())
    return [error.message for error in validator.iter_errors(message)]


def example(name: str) -> dict:
    """A valid example message, e.g. "init.standard"."""
    return json.loads((PROTOCOL / "examples" / "valid" / f"{name}.json").read_text("utf-8"))


def examples(prefix: str) -> list[Path]:
    return sorted((PROTOCOL / "examples" / "valid").glob(f"{prefix}.*.json"))
