"""Every Board and Move function of spec/api/ exists with its kind and parameter count."""

import inspect

import pytest
import spec_files

import sbm

FUNCTIONS = spec_files.core_functions()


def parameter_count(member) -> int:
    """Parameters of a nanobind function, read from its signature line in the docstring."""
    signature = member.__doc__.splitlines()[0]
    inside = signature[signature.index("(") + 1 : signature.rindex(")")]
    names = [part.split(":")[0].strip() for part in inside.split(",") if part.strip()]
    return len([name for name in names if name != "self"])


@pytest.mark.parametrize("name", sorted(FUNCTIONS))
def test_function_exists(name):
    function = FUNCTIONS[name]
    owner = getattr(sbm, function["owner"])
    expected = len(function["params"])
    if function["kind"] == "constructor":
        assert parameter_count(owner.__init__) == expected
        return
    member = inspect.getattr_static(owner, function["name"])
    is_static = isinstance(member, staticmethod) or type(member).__name__ == "nb_func"
    if function["kind"] == "static":
        assert is_static
    else:
        assert type(member).__name__ == "nb_method"
    assert parameter_count(getattr(owner, function["name"])) == expected
