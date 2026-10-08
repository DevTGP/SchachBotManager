"""sbm-check: file selection, exit codes and output; the template and reference bots pass."""

import json
import os
from pathlib import Path

import pytest

import sbm.bots
from sbm.analysis import check_project, select_files
from sbm.analysis.cli import main

TEMPLATE = Path(__file__).resolve().parents[3] / "templates" / "python"
REFERENCE_BOTS = Path(sbm.bots.__file__).parent


def make_bot(root: Path, files: dict[str, str]) -> Path:
    for path, text in files.items():
        file = root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text, encoding="utf-8")
    return root


def test_selection(tmp_path):
    make_bot(
        tmp_path,
        {
            "bot.py": "",
            "engine/search.py": "",
            "engine/__pycache__/search.cpython-312.pyc": "",
            ".venv/lib/x.py": "",
            ".hidden.py": "",
            "README.md": "",
            "data/book.txt": "",
            "data/sub/deep.txt": "",
            "tests/test_bot.py": "",
        },
    )
    selection = select_files(tmp_path, ["tests/*"])
    assert sorted(selection.files) == ["bot.py", "data/book.txt", "engine/search.py"]
    assert selection.files["bot.py"] == tmp_path / "bot.py"
    assert sorted(selection.ignored) == ["README.md", "data/sub/deep.txt"]


@pytest.mark.skipif(os.name == "nt", reason="symbolic links need extra rights on Windows")
def test_selection_skips_links(tmp_path):
    make_bot(tmp_path, {"bot.py": ""})
    (tmp_path / "link.py").symlink_to(tmp_path / "bot.py")
    assert sorted(select_files(tmp_path).files) == ["bot.py"]


def test_template_passes(capsys):
    assert main([str(TEMPLATE)]) == 0
    out = capsys.readouterr()
    assert out.out.strip() == "sbm-check: OK, 2 files checked (python-1)"
    assert "README.md" in out.err


@pytest.mark.parametrize("entry", ["random_mover.py", "material.py"])
def test_reference_bots_pass(entry):
    report = check_project(select_files(REFERENCE_BOTS), entry)
    assert report.findings == ()


def test_findings(tmp_path, capsys):
    make_bot(tmp_path, {"bot.py": "import os\n", "util.py": "x = eval('1')\n"})
    assert main([str(tmp_path)]) == 1
    lines = capsys.readouterr().out.splitlines()
    assert lines == [
        "bot.py:1: import_not_allowed: import os is not allowed",
        "util.py:1: forbidden_name: the name eval is not allowed",
        "sbm-check: 2 problems in 2 files (python-1)",
    ]


def test_upload_problem_and_analysis(tmp_path, capsys):
    make_bot(tmp_path, {"main.py": "import os\n"})
    assert main([str(tmp_path), "--json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert [finding["rule"] for finding in report["findings"]] == ["upload", "import_not_allowed"]
    assert report["findings"][0]["file"] == "bot.py"


def test_entry_option(tmp_path, capsys):
    make_bot(tmp_path, {"main.py": "x = 1\n"})
    assert main([str(tmp_path), "--entry", "main.py", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "ruleset": "python-1",
        "ok": True,
        "truncated": False,
        "findings": [],
    }


def test_missing_folder(tmp_path):
    with pytest.raises(SystemExit) as error:
        main([str(tmp_path / "missing")])
    assert error.value.code == 2
