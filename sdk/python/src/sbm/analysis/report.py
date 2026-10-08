"""Findings and the report of an analysis; the JSON form is what the runner reads."""

from dataclasses import dataclass

UPLOAD = "upload"
ENCODING = "encoding"
SYNTAX_ERROR = "syntax_error"
IMPORT_NOT_ALLOWED = "import_not_allowed"
SHADOWED_MODULE = "shadowed_module"
FORBIDDEN_NAME = "forbidden_name"
DUNDER = "dunder"
PRIVATE_ATTRIBUTE = "private_attribute"
MODULE_VALUE = "module_value"


@dataclass(frozen=True)
class Finding:
    file: str
    line: int | None
    rule: str
    message: str

    def to_json(self) -> dict:
        return {"rule": self.rule, "file": self.file, "line": self.line, "message": self.message}

    def text(self) -> str:
        place = self.file if self.line is None else f"{self.file}:{self.line}"
        return f"{place}: {self.rule}: {self.message}"


@dataclass(frozen=True)
class Report:
    ruleset: str
    findings: tuple[Finding, ...]
    truncated: bool = False

    @property
    def ok(self) -> bool:
        return not self.findings

    def to_json(self) -> dict:
        return {
            "ruleset": self.ruleset,
            "ok": self.ok,
            "truncated": self.truncated,
            "findings": [finding.to_json() for finding in self.findings],
        }


def make_report(ruleset: str, findings: list[Finding], limit: int) -> Report:
    """Sorted by file and line, at most limit findings."""
    ordered = sorted(set(findings), key=lambda f: (f.file, f.line or 0, f.rule, f.message))
    return Report(ruleset, tuple(ordered[:limit]), truncated=len(ordered) > limit)
