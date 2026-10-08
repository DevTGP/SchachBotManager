"""The Python analyzer: what a bot may write and what it may not (statische-analyse.md)."""

import textwrap

import pytest

from sbm.analysis import analyze, load_rules


def check(source: str, **more: str) -> list[tuple[str, str, int | None]]:
    files = {"bot.py": source, **more}
    report = analyze({path: textwrap.dedent(text).encode() for path, text in files.items()})
    return [(finding.rule, finding.file, finding.line) for finding in report.findings]


def rules_of(source: str, **more: str) -> set[str]:
    return {rule for rule, _, _ in check(source, **more)}


ALLOWED = {
    "bot": """
        '''A bot with a __docstring__ that names __init__.'''
        from __future__ import annotations

        import random
        import collections.abc
        from dataclasses import dataclass, field
        from typing import Optional

        import sbm
        from sbm import Bot, Board, Move, load_data, run


        @dataclass
        class Entry:
            moves: list[str] = field(default_factory=list)


        class MyBot(Bot):
            __slots__ = ("_book",)

            def __init__(self) -> None:
                super().__init__()
                self._book: Optional[bytes] = None

            def __eq__(self, other: object) -> bool:
                return isinstance(other, MyBot) and self._book is None

            def choose_move(self, board: Board, clock) -> Move:
                if isinstance(board, collections.abc.Hashable):
                    pass
                return random.choice(board.legal_moves())

            @classmethod
            def make(cls):
                return cls._create()

            @classmethod
            def _create(cls):
                return cls()


        if __name__ == "__main__":
            run(MyBot())
    """,
    "match": """
        def f(point):
            match point:
                case {"x": x}:
                    return x
                case _:
                    return sbm_value
    """,
    "type hint text": """
        def f(board: "Board") -> "list[int]":
            return []
    """,
    "f-string": """
        name = "x"
        text = f"{name!r} at {1:>4}"
    """,
}


@pytest.mark.parametrize("source", ALLOWED.values(), ids=ALLOWED.keys())
def test_allowed(source):
    assert check(source) == []


REJECTED = {
    "import os": ("import os", "import_not_allowed"),
    "import os.path": ("import os.path", "import_not_allowed"),
    "from os": ("from os import system", "import_not_allowed"),
    "importlib": ("import importlib", "import_not_allowed"),
    "numpy": ("import numpy", "import_not_allowed"),
    "submodule": ("import collections.defaultdict", "import_not_allowed"),
    "sdk internals": ("from sbm import _core", "private_attribute"),
    "sdk module": ("from sbm import runtime", "import_not_allowed"),
    "sdk attribute": ("import sbm\nsbm.arena.cli", "module_value"),
    "sdk analysis": ("import sbm\nx = sbm.analysis", "module_value"),
    "eval": ("eval('1')", "forbidden_name"),
    "exec": ("exec('1')", "forbidden_name"),
    "open": ("open('x')", "forbidden_name"),
    "getattr": ("getattr(1, 'real')", "forbidden_name"),
    "import builtin": ("__import__('os')", "dunder"),
    "builtins name": ("__builtins__", "dunder"),
    "dunder attribute": ("x = ().__class__", "dunder"),
    "subclasses": ("object.__subclasses__()", "dunder"),
    "dunder string": ("name = '__class__'", "dunder"),
    "dunder bytes": ("name = b'__globals__'", "dunder"),
    "dunder in f-string": ("x = 1\nname = f'__dict__{x}'", "dunder"),
    "private module": ("import random\nrandom._os", "private_attribute"),
    "private from": ("from random import _os", "private_attribute"),
    "private elsewhere": ("x = Thing()\nx._secret", "private_attribute"),
    "private on other": ("def f(self, other):\n    return other._book", "private_attribute"),
    "module attribute": ("import dataclasses\ndataclasses.sys.modules", "module_value"),
    "builtins via enum": ("import enum\nenum.bltns", "module_value"),
    "module via typing": ("from typing import sys", "import_not_allowed"),
    "module as value": ("import random\nr = random", "module_value"),
    "module as argument": ("import random\nprint(random)", "module_value"),
    "frame": ("def g():\n    yield\ng().gi_frame", "forbidden_name"),
    "frame globals": ("frame.f_globals", "forbidden_name"),
    "type hints": ("import typing\ntyping.get_type_hints(int)", "forbidden_name"),
    "forward ref": ("from typing import ForwardRef", "forbidden_name"),
    "attrgetter": ("import operator\noperator.attrgetter('x')", "forbidden_name"),
    "match attribute": ("match x:\n    case object(__class__=c):\n        pass", "dunder"),
    "match private": ("match x:\n    case object(_secret=s):\n        pass", "private_attribute"),
    "dunder alias": ("import random as __builtins__", "dunder"),
    "syntax": ("def f(:\n    pass", "syntax_error"),
    "null byte": ("x = 1\0", "syntax_error"),
    "relative outside": ("from .. import x", None),
}


@pytest.mark.parametrize("source, rule", REJECTED.values(), ids=REJECTED.keys())
def test_rejected(source, rule):
    rules = rules_of(source)
    if rule is None:
        assert rules == set()
    else:
        assert rule in rules


def test_reports_file_and_line():
    assert check("x = 1\n\nimport os\n") == [("import_not_allowed", "bot.py", 3)]


def test_own_modules_may_be_imported():
    helper = "import random\n\ndef pick(items):\n    return random.choice(items)\n"
    source = "import helper\nfrom engine import search\nfrom engine.search import best\n"
    source += "helper.pick([1])\nhelper._cache\n"
    files = {
        "helper.py": helper,
        "engine/__init__.py": "",
        "engine/search.py": "from . import tables\nfrom .tables import VALUES\nbest = 1\n",
        "engine/tables.py": "VALUES = [1]\n",
    }
    assert check(source, **files) == []


@pytest.mark.parametrize(
    "source",
    [
        "import helper\nhelper.dataclasses.sys",
        "import helper\nhelper.random._os",
        "import helper\nx = helper.random",
        "from helper import random\nrandom._os",
        "from helper import *\nx = dataclasses",
        "from helper import _dc\n_dc.sys",
    ],
)
def test_modules_through_own_modules(source):
    helper = "import random\nimport dataclasses\nimport dataclasses as _dc\n"
    assert rules_of(source, **{"helper.py": helper}) & {"module_value", "private_attribute"}


def test_own_modules_cannot_carry_forbidden_modules():
    assert rules_of("import helper", **{"helper.py": "import os"}) == {"import_not_allowed"}


def test_data_folder_is_not_importable():
    assert "import_not_allowed" in rules_of("import data.book")


@pytest.mark.parametrize("path", ["json.py", "random.py", "sbm/__init__.py", "typing/x.py"])
def test_shadowed_modules(path):
    assert ("shadowed_module", path, None) in check("x = 1", **{path: "y = 2"})


def test_module_defined_twice():
    rules = rules_of("x = 1", **{"tools.py": "", "tools/__init__.py": ""})
    assert "shadowed_module" in rules


@pytest.mark.parametrize(
    "source",
    [
        b"# coding: utf-7\nx = 1\n",
        b"#!/usr/bin/env python\n# -*- coding: latin-1 -*-\nx = 1\n",
        b"x = '\xff'\n",
    ],
)
def test_encoding(source):
    report = analyze({"bot.py": source})
    assert [finding.rule for finding in report.findings] == ["encoding"]


def test_utf8_declaration_and_bom_are_fine():
    assert analyze({"bot.py": b"\xef\xbb\xbf# coding: utf-8\nx = 'a'\n"}).ok


def test_deep_nesting_is_a_finding():
    source = ("x = " + "(" * 5000 + "1" + ")" * 5000 + "\n").encode()
    report = analyze({"bot.py": source})
    assert [finding.rule for finding in report.findings] == ["syntax_error"]


def test_long_attribute_chain():
    # Longer than the recursion limit, short enough for the parser.
    source = ("x = y" + ".a" * 2000 + "\n").encode()
    assert analyze({"bot.py": source}).ok


def test_findings_are_capped():
    limit = load_rules().max_findings
    report = analyze({"bot.py": ("eval\n" * (limit + 5)).encode()})
    assert len(report.findings) == limit
    assert report.truncated


def test_report_json():
    report = analyze({"bot.py": b"import os\n"})
    assert report.to_json() == {
        "ruleset": "python-1",
        "ok": False,
        "truncated": False,
        "findings": [
            {
                "rule": "import_not_allowed",
                "file": "bot.py",
                "line": 1,
                "message": "import os is not allowed",
            }
        ],
    }
