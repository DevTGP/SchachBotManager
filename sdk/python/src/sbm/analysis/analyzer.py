"""Analyzes all source files of a Python bot at once (statische-analyse.md).

The analyzer only parses; it never imports or runs the bot. On the server it runs in the sandbox
like the bot itself (E81).
"""

import ast
import re
import sys
from collections.abc import Mapping

from sbm.analysis.checker import FileChecker
from sbm.analysis.modules import Modules, module_name
from sbm.analysis.report import (
    ENCODING,
    SHADOWED_MODULE,
    SYNTAX_ERROR,
    Finding,
    Report,
    make_report,
)
from sbm.analysis.rules import Rules, load_rules

# PEP 263: a coding declaration in one of the first two lines.
_CODING = re.compile(rb"^[ \t\f]*#.*?coding[:=][ \t]*([-\w.]+)", re.MULTILINE)
_UTF8_NAMES = {"utf-8", "utf8", "utf_8", "utf-8-sig"}


def analyze(sources: Mapping[str, bytes], rules: Rules | None = None) -> Report:
    """sources maps the paths of all .py files (relative, with /) to their contents."""
    rules = rules or load_rules()
    findings: list[Finding] = []
    paths: dict[str, str] = {}
    trees: dict[str, ast.Module] = {}
    for path in sorted(sources):
        name = module_name(path)
        if name in paths:
            findings.append(
                Finding(path, None, SHADOWED_MODULE, f"{paths[name]} also defines module {name}")
            )
            continue
        paths[name] = path
        tree = _parse(path, sources[path], findings)
        if tree is not None:
            trees[name] = tree
    findings.extend(_shadowed(paths, rules))
    modules = Modules(rules, trees, paths)
    for name, tree in trees.items():
        findings.extend(modules.bindings(name).findings)
        findings.extend(FileChecker(modules, name, tree).check())
    return make_report(rules.ruleset, findings, rules.max_findings)


def _parse(path: str, source: bytes, findings: list[Finding]) -> ast.Module | None:
    head = b"\n".join(source.split(b"\n", 2)[:2])
    declared = _CODING.search(head)
    if declared and declared.group(1).decode("ascii", "replace").lower() not in _UTF8_NAMES:
        findings.append(Finding(path, None, ENCODING, "files must be UTF-8"))
        return None
    try:
        source.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        findings.append(Finding(path, None, ENCODING, f"not valid UTF-8: {error.reason}"))
        return None
    try:
        # Parsed from bytes, so Python reads the file exactly as it will when the bot runs.
        return ast.parse(source, filename=path)
    except SyntaxError as error:
        findings.append(Finding(path, error.lineno, SYNTAX_ERROR, error.msg))
    except (ValueError, RecursionError, MemoryError) as error:
        message = str(error) or "the file is nested too deeply"
        findings.append(Finding(path, None, SYNTAX_ERROR, message))
    return None


def _shadowed(paths: dict[str, str], rules: Rules) -> list[Finding]:
    """An own module must not hide one of Python's, of the whitelist or of the SDK."""
    reserved = (
        set(sys.stdlib_module_names)
        | {name.split(".")[0] for name in rules.modules}
        | rules.reserved_modules
    )
    findings = {}
    for name, path in sorted(paths.items(), key=lambda item: item[1]):
        top = name.split(".")[0]
        if top in reserved and top not in findings:
            findings[top] = Finding(
                path, None, SHADOWED_MODULE, f"the module name {top} is taken by Python or the SDK"
            )
    return list(findings.values())
