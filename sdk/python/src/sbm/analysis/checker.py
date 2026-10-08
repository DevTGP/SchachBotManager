"""The rules a single file must follow (statische-analyse.md); imports resolve in modules.py."""

import ast
import re

from sbm.analysis.modules import ModuleRef, Modules
from sbm.analysis.report import (
    DUNDER,
    FORBIDDEN_NAME,
    MODULE_VALUE,
    PRIVATE_ATTRIBUTE,
    Finding,
)

_DUNDER_IN_TEXT = re.compile(r"__\w+?__")


def is_dunder(name: str) -> bool:
    return len(name) > 4 and name.startswith("__") and name.endswith("__")


def _may_resolve(ref: ModuleRef, name: str) -> bool:
    """Private names of whitelisted modules are reported, not followed."""
    return not is_dunder(name) and (ref.own or not name.startswith("_"))


class FileChecker:
    def __init__(self, modules: Modules, module: str, tree: ast.Module) -> None:
        self._modules = modules
        self._rules = modules.rules
        self._path = modules.paths[module]
        self._tree = tree
        self._names = modules.bindings(module).names
        self._parents: dict[int, ast.AST] = {}
        self._refs: dict[int, ModuleRef | None] = {}
        self.findings: list[Finding] = []

    def check(self) -> list[Finding]:
        docstrings = set()
        for node in ast.walk(self._tree):
            for child in ast.iter_child_nodes(node):
                self._parents[id(child)] = node
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                first = node.body[0] if node.body else None
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                    docstrings.add(id(first.value))
        for node in ast.walk(self._tree):
            if isinstance(node, ast.Name):
                self._name(node)
            elif isinstance(node, ast.Attribute):
                self._attribute(node)
            elif isinstance(node, ast.MatchClass):
                for name in node.kwd_attrs:
                    self._attribute_name(node, name, base=None)
            elif isinstance(node, ast.ImportFrom):
                self._import_from(node)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    self._binding_name(node, alias.asname)
            elif isinstance(node, ast.Constant) and id(node) not in docstrings:
                self._constant(node)
        return self.findings

    def _report(self, node: ast.AST, rule: str, message: str) -> None:
        self.findings.append(Finding(self._path, getattr(node, "lineno", None), rule, message))

    def _name(self, node: ast.Name) -> None:
        name = node.id
        if is_dunder(name):
            allowed = {
                ast.Load: self._rules.dunder_loads,
                ast.Store: self._rules.dunder_stores,
            }.get(type(node.ctx), frozenset())
            if name not in allowed:
                self._report(node, DUNDER, f"the name {name} is not allowed")
            return
        if name in self._rules.forbidden_builtins:
            self._report(node, FORBIDDEN_NAME, f"the name {name} is not allowed")
            return
        if isinstance(node.ctx, ast.Load) and self._module_ref(node) is not None:
            self._check_dotted_use(node, name)

    def _attribute(self, node: ast.Attribute) -> None:
        self._attribute_name(node, node.attr, base=node.value)
        base_ref = self._module_ref(node.value)
        if base_ref is None or not _may_resolve(base_ref, node.attr):
            return
        result = self._modules.attribute(base_ref, node.attr)
        if isinstance(result, str):
            self._report(node, MODULE_VALUE, result)
        elif result is not None:
            self._check_dotted_use(node, result.name)

    def _attribute_name(self, node: ast.AST, name: str, base: ast.expr | None) -> None:
        if is_dunder(name):
            if name not in self._rules.dunder_attributes:
                self._report(node, DUNDER, f"the attribute {name} is not allowed")
        elif name.startswith("_") and not self._private_allowed(base):
            self._report(
                node,
                PRIVATE_ATTRIBUTE,
                f"the attribute {name} may only be used on self, cls, super() or own modules",
            )
        elif name in self._rules.forbidden_attributes:
            self._report(node, FORBIDDEN_NAME, f"the attribute {name} is not allowed")

    def _private_allowed(self, base: ast.expr | None) -> bool:
        if isinstance(base, ast.Name) and base.id in self._rules.private_bases:
            return True
        if (
            isinstance(base, ast.Call)
            and isinstance(base.func, ast.Name)
            and base.func.id == "super"
        ):
            return True
        ref = self._module_ref(base) if base is not None else None
        return ref is not None and ref.own

    def _import_from(self, node: ast.ImportFrom) -> None:
        own = node.level > 0 or (node.module or "").split(".")[0] in self._modules.own
        for alias in node.names:
            if alias.name != "*":
                if not own and alias.name.startswith("_"):
                    self._attribute_name(node, alias.name, base=None)
                elif alias.name in self._rules.forbidden_attributes:
                    self._report(node, FORBIDDEN_NAME, f"the name {alias.name} is not allowed")
            self._binding_name(node, alias.asname)

    def _binding_name(self, node: ast.AST, name: str | None) -> None:
        if name is not None and is_dunder(name) and name not in self._rules.dunder_stores:
            self._report(node, DUNDER, f"the name {name} is not allowed")

    def _constant(self, node: ast.Constant) -> None:
        value = node.value
        if isinstance(value, bytes):
            value = value.decode("latin-1")
        if not isinstance(value, str):
            return
        for match in _DUNDER_IN_TEXT.finditer(value):
            if match.group() not in self._rules.dunder_strings:
                self._report(node, DUNDER, f"the text {match.group()} is not allowed in strings")
                return

    def _check_dotted_use(self, node: ast.expr, name: str) -> None:
        """A module may only be used with a dot, never be passed on or stored."""
        parent = self._parents.get(id(node))
        if not (isinstance(parent, ast.Attribute) and parent.value is node):
            self._report(node, MODULE_VALUE, f"the module {name} may only be used as module.name")

    def _module_ref(self, node: ast.expr) -> ModuleRef | None:
        """The module an expression stands for, following attribute chains without recursion."""
        chain: list[ast.Attribute] = []
        while isinstance(node, ast.Attribute) and id(node) not in self._refs:
            chain.append(node)
            node = node.value
        if isinstance(node, ast.Attribute):
            ref = self._refs[id(node)]
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            ref = self._names.get(node.id)
        else:
            ref = None
        for attribute in reversed(chain):
            if ref is not None and _may_resolve(ref, attribute.attr):
                result = self._modules.attribute(ref, attribute.attr)
                ref = result if isinstance(result, ModuleRef) else None
            else:
                ref = None
            self._refs[id(attribute)] = ref
        return ref
