from pathlib import Path

from spec_check.check import check_spec


def test_valid_and_invalid_examples_behave_as_expected(spec_root: Path, write_json, ping_schema):
    write_json("protocol/v1/examples/valid/ping.basic.json", {"type": "ping", "v": 1})
    write_json("protocol/v1/examples/invalid/ping.wrong_version.json", {"type": "ping", "v": 2})

    assert check_spec(spec_root) == []


def test_valid_example_violating_schema_is_reported(spec_root: Path, write_json, ping_schema):
    example = write_json(
        "protocol/v1/examples/valid/ping.extra.json", {"type": "ping", "v": 1, "x": 0}
    )

    problems = check_spec(spec_root)

    assert [p.path for p in problems] == [example]


def test_invalid_example_passing_schema_is_reported(spec_root: Path, write_json, ping_schema):
    example = write_json("protocol/v1/examples/invalid/ping.ok.json", {"type": "ping", "v": 1})

    problems = check_spec(spec_root)

    assert [p.path for p in problems] == [example]
    assert "passes its schema" in problems[0].message


def test_example_outside_expectation_folder_is_reported(spec_root: Path, write_json, ping_schema):
    example = write_json("protocol/v1/examples/ping.basic.json", {"type": "ping", "v": 1})

    problems = check_spec(spec_root)

    assert [p.path for p in problems] == [example]


def test_example_without_schema_is_reported(spec_root: Path, write_json):
    example = write_json("protocol/v1/examples/valid/pong.basic.json", {"type": "pong"})

    problems = check_spec(spec_root)

    assert [p.path for p in problems] == [example]
    assert "pong.schema.json" in problems[0].message
