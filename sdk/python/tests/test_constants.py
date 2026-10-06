"""Constants of the package against spec/api/constants.json."""

import pytest
import spec_files

import sbm

CONSTANTS = spec_files.constants()


@pytest.mark.parametrize("constant", CONSTANTS, ids=[c["name"] for c in CONSTANTS])
def test_constant(constant):
    value = getattr(sbm, constant["name"])
    if constant["type"] == "Move":
        assert value == sbm.Move.from_value(constant["value"])
        assert getattr(sbm.Move, constant["name"]) == value
    else:
        assert type(value) is int
        assert value == constant["value"]


def test_no_extra_constants():
    names = {constant["name"] for constant in CONSTANTS}
    exported = {name for name in sbm.__all__ if name.isupper()}
    assert exported == names
