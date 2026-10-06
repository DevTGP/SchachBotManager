from pathlib import Path

from spec_check.loading import load_json_files


def test_loads_nested_json_files(spec_root: Path, write_json):
    path = write_json("a/b/doc.json", {"x": 1})

    documents, problems = load_json_files(spec_root)

    assert documents == {path: {"x": 1}}
    assert problems == []


def test_reports_malformed_json(spec_root: Path):
    broken = spec_root / "broken.json"
    broken.write_text("{not json", encoding="utf-8")

    documents, problems = load_json_files(spec_root)

    assert documents == {}
    assert [p.path for p in problems] == [broken]
    assert "invalid JSON" in problems[0].message
