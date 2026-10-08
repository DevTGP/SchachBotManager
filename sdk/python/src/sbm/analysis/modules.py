"""Which names refer to modules: the bot's own modules and those on the whitelist.

A bot must never get hold of a module outside the whitelist. Whitelisted modules carry other
modules as attributes (dataclasses.sys, enum.bltns, random._os), so the analyzer follows every
module reference: through imports, star imports and attributes, also through the bot's own
modules. Names are tracked per file without scopes; that errs towards treating more as a module.
"""

import ast
import importlib
import inspect
from dataclasses import dataclass, field

import sbm
from sbm.analysis.report import IMPORT_NOT_ALLOWED, Finding
from sbm.analysis.rules import Rules


@dataclass(frozen=True)
class ModuleRef:
    name: str
    own: bool


@dataclass
class Bindings:
    """Names a file binds to modules, and the findings its imports gave."""

    names: dict[str, ModuleRef] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)


def module_name(path: str) -> str:
    """The dotted name a source path is imported by: a/b.py is a.b, a/__init__.py is a."""
    parts = path[: -len(".py")].split("/")
    if parts[-1] == "__init__" and len(parts) > 1:
        parts.pop()
    return ".".join(parts)


class Modules:
    def __init__(self, rules: Rules, trees: dict[str, ast.Module], paths: dict[str, str]) -> None:
        """trees maps module names to parsed files, paths module names to their paths."""
        self.rules = rules
        self._trees = trees
        self.paths = paths
        self.own: set[str] = set()
        for name in paths:
            parts = name.split(".")
            # Every folder on the way is a package, with or without __init__.py.
            self.own.update(".".join(parts[:end]) for end in range(1, len(parts) + 1))
        self._bindings: dict[str, Bindings] = {}
        self._in_progress: set[str] = set()

    def bindings(self, module: str) -> Bindings:
        if module in self._bindings:
            return self._bindings[module]
        if module in self._in_progress or module not in self._trees:
            return Bindings()
        self._in_progress.add(module)
        try:
            result = _Binder(self, module).bind(self._trees[module])
        finally:
            self._in_progress.discard(module)
        self._bindings[module] = result
        return result

    def is_package(self, module: str) -> bool:
        path = self.paths.get(module)
        return path is None or path.endswith("/__init__.py") or path == "__init__.py"

    def attribute(self, ref: ModuleRef, name: str) -> ModuleRef | str | None:
        """The module ref.name is, a message if it must not be used, None for no module."""
        if ref.own:
            child = f"{ref.name}.{name}"
            if child in self.own:
                return ModuleRef(child, own=True)
            return self.bindings(ref.name).names.get(name)
        if ref.name == "sbm" and name not in sbm.__all__:
            return f"sbm.{name} is not part of the SDK"
        value = getattr(importlib.import_module(ref.name), name, None)
        if not inspect.ismodule(value):
            return None
        if value.__name__ in self.rules.modules:
            return ModuleRef(value.__name__, own=False)
        return f"{ref.name}.{name} is the module {value.__name__}, which is not allowed"

    def star_names(self, ref: ModuleRef) -> dict[str, ModuleRef] | str:
        """What from ref.name import * binds to modules."""
        if ref.own:
            # Errs on the safe side: every binding, every submodule.
            names = dict(self.bindings(ref.name).names)
            prefix = f"{ref.name}."
            for child in self.own:
                if child.startswith(prefix) and "." not in child[len(prefix) :]:
                    names[child[len(prefix) :]] = ModuleRef(child, own=True)
            return names
        module = importlib.import_module(ref.name)
        exported = getattr(module, "__all__", None)
        if exported is None:
            exported = [name for name in dir(module) if not name.startswith("_")]
        names = {}
        for name in exported:
            result = self.attribute(ref, name)
            if isinstance(result, str):
                return result
            if result is not None:
                names[name] = result
        return names


class _Binder:
    """Collects the module bindings of one file from its import statements."""

    def __init__(self, modules: Modules, module: str) -> None:
        self._modules = modules
        self._module = module
        self._path = modules.paths[module]
        self._result = Bindings()

    def bind(self, tree: ast.Module) -> Bindings:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self._import(node)
            elif isinstance(node, ast.ImportFrom):
                self._import_from(node)
        return self._result

    def _fail(self, node: ast.AST, message: str) -> None:
        self._result.findings.append(
            Finding(self._path, getattr(node, "lineno", None), IMPORT_NOT_ALLOWED, message)
        )

    def _import(self, node: ast.Import) -> None:
        for alias in node.names:
            top = alias.name.split(".")[0]
            if top in self._modules.own:
                own = True
            elif alias.name in self._modules.rules.modules:
                own = False
            else:
                self._fail(node, f"import {alias.name} is not allowed")
                continue
            if alias.asname:
                self._result.names[alias.asname] = ModuleRef(alias.name, own)
            else:
                self._result.names[top] = ModuleRef(top, own)

    def _import_from(self, node: ast.ImportFrom) -> None:
        source = self._source(node)
        if source is None:
            return
        if isinstance(source, str):
            self._fail(node, source)
            return
        for alias in node.names:
            if alias.name == "*":
                names = self._modules.star_names(source)
                if isinstance(names, str):
                    self._fail(node, names)
                else:
                    self._result.names.update(names)
                continue
            if not source.own and alias.name.startswith("_"):
                continue  # The checker reports it as a private name.
            result = self._modules.attribute(source, alias.name)
            if isinstance(result, str):
                self._fail(node, result)
            elif result is not None:
                self._result.names[alias.asname or alias.name] = result

    def _source(self, node: ast.ImportFrom) -> ModuleRef | str | None:
        """The module imported from; None if the import cannot reach outside the bot."""
        if node.level == 0:
            name = node.module or ""
            if name.split(".")[0] in self._modules.own:
                return ModuleRef(name, own=True)
            if name in self._modules.rules.modules:
                return ModuleRef(name, own=False)
            return f"import from {name} is not allowed"
        package = self._module.split(".")
        if not self._modules.is_package(self._module):
            package.pop()
        if node.level - 1 > len(package):
            return None  # Fails at run time: beyond the top folder.
        base = package[: len(package) - (node.level - 1)]
        if node.module:
            base.append(node.module)
        if not base:
            return None  # A relative import in the top folder fails at run time.
        return ModuleRef(".".join(base), own=True)
