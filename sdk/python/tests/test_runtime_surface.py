"""Clock, Log, Bot, run, load_data and the records of spec/api/ exist with their parameters."""

import dataclasses
import inspect

import pytest
import spec_files

import sbm

RUNTIME_MODULES = ["bot", "clock", "log", "runtime"]
FUNCTIONS = [
    function
    for module in RUNTIME_MODULES
    for function in spec_files.load(spec_files.SPEC / "api" / f"{module}.json")["functions"]
]
RECORDS = [
    record
    for record in spec_files.load(spec_files.SPEC / "api" / "types.json")["types"]
    if record["kind"] == "record"
]


def full_name(function: dict) -> str:
    owner = function.get("owner")
    return f"{owner}.{function['name']}" if owner else function["name"]


@pytest.mark.parametrize("function", FUNCTIONS, ids=full_name)
def test_function_exists(function):
    owner = getattr(sbm, function["owner"]) if function.get("owner") else sbm
    member = inspect.getattr_static(owner, function["name"])
    if function["kind"] == "static":
        assert isinstance(member, staticmethod)
    elif function["kind"] in ("method", "callback"):
        assert inspect.isfunction(member)
    parameters = [
        name
        for name in inspect.signature(getattr(owner, function["name"])).parameters
        if name != "self"
    ]
    assert parameters == [parameter["name"] for parameter in function["params"]]


def test_choose_move_is_the_only_required_callback():
    assert sbm.Bot.__abstractmethods__ == {"choose_move"}


@pytest.mark.parametrize("record", RECORDS, ids=lambda record: record["name"])
def test_record_fields(record):
    cls = getattr(sbm, record["name"])
    assert [field.name for field in dataclasses.fields(cls)] == [
        field["name"] for field in record["fields"]
    ]
    assert cls.__dataclass_params__.frozen == (record["name"] != "Info")
