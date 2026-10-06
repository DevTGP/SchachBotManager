from pathlib import Path

from testvector_gen import cli


def test_missing_directory(tmp_path: Path):
    assert cli.main([str(tmp_path)]) == 2


def test_check_reports_missing_differing_and_extra(tmp_path: Path):
    directory = tmp_path / "testvectors"
    expected = {"a.json": "A\n", "sub/b.json": "B\n"}
    cli.write(directory, expected)
    assert cli.check(directory, expected) == []

    (directory / "a.json").write_text("changed\n", encoding="utf-8")
    (directory / "sub/b.json").unlink()
    (directory / "extra.json").write_text("{}", encoding="utf-8")
    (directory / "kept.schema.json").write_text("{}", encoding="utf-8")
    assert cli.check(directory, expected) == [
        "a.json: differs",
        "sub/b.json: missing",
        "extra.json: not generated",
    ]


def test_write_then_check(tmp_path: Path):
    (tmp_path / "testvectors").mkdir()
    assert cli.main([str(tmp_path)]) == 0
    assert cli.main([str(tmp_path), "--check"]) == 0
    assert b"\r" not in (tmp_path / "testvectors/api/move.json").read_bytes()
