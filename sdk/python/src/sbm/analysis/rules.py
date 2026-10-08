"""The versioned rule set of the Python analyzer (statische-analyse.md), read from JSON."""

import json
from dataclasses import dataclass
from importlib import resources

RULES_FILE = "python_rules.json"


@dataclass(frozen=True)
class Rules:
    ruleset: str
    modules: frozenset[str]
    reserved_modules: frozenset[str]
    forbidden_builtins: frozenset[str]
    forbidden_attributes: frozenset[str]
    dunder_loads: frozenset[str]
    dunder_stores: frozenset[str]
    dunder_attributes: frozenset[str]
    dunder_strings: frozenset[str]
    private_bases: frozenset[str]
    max_findings: int

    @classmethod
    def from_json(cls, data: dict) -> "Rules":
        return cls(
            ruleset=data["ruleset"],
            max_findings=data["max_findings"],
            **{
                name: frozenset(data[name])
                for name in cls.__dataclass_fields__
                if name not in ("ruleset", "max_findings")
            },
        )


def load_rules() -> Rules:
    text = resources.files(__package__).joinpath(RULES_FILE).read_text(encoding="utf-8")
    return Rules.from_json(json.loads(text))
