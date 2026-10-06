from pathlib import Path

from spec_check.cli import EXIT_OK, EXIT_PROBLEMS, EXIT_USAGE, main


def test_empty_spec_is_ok(spec_root: Path, capsys):
    assert main([str(spec_root)]) == EXIT_OK
    assert "OK" in capsys.readouterr().out


def test_problems_are_printed_with_relative_paths(spec_root: Path, capsys):
    (spec_root / "sub").mkdir()
    (spec_root / "sub" / "broken.json").write_text("{", encoding="utf-8")

    assert main([str(spec_root)]) == EXIT_PROBLEMS
    assert capsys.readouterr().out.startswith("sub/broken.json: invalid JSON")


def test_missing_directory_is_a_usage_error(tmp_path: Path):
    assert main([str(tmp_path / "missing")]) == EXIT_USAGE
