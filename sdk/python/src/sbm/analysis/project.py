"""Checks a bot folder as it would be uploaded: which files count, the upload rules, the analysis.

sbm-check and the runner use it alike; in the runner the folder holds exactly the uploaded files.
"""

import fnmatch
import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from sbm.analysis.analyzer import analyze
from sbm.analysis.report import UPLOAD, Finding, Report, make_report
from sbm.analysis.rules import Rules, load_rules
from sbm.analysis.upload import DATA_DIR, UploadError, check_upload

_SKIPPED_FOLDERS = {"__pycache__"}


@dataclass(frozen=True)
class Selection:
    """files maps upload paths to files on disk; ignored lists what an upload would leave out."""

    files: dict[str, Path]
    ignored: list[str]


def select_files(root: Path, excludes: Sequence[str] = ()) -> Selection:
    """.py files outside hidden folders and __pycache__, and the files directly in data/."""
    files: dict[str, Path] = {}
    ignored: list[str] = []
    for folder, subfolders, names in os.walk(root):
        relative = Path(folder).relative_to(root).as_posix()
        prefix = "" if relative == "." else f"{relative}/"
        subfolders[:] = sorted(
            name
            for name in subfolders
            if not name.startswith(".")
            and name not in _SKIPPED_FOLDERS
            and not _excluded(f"{prefix}{name}", excludes)
        )
        for name in sorted(names):
            path = f"{prefix}{name}"
            if name.startswith(".") or _excluded(path, excludes):
                continue
            in_data = path.startswith(f"{DATA_DIR}/")
            wanted = path.count("/") == 1 if in_data else name.endswith(".py")
            if wanted and not os.path.islink(os.path.join(folder, name)):
                files[path] = Path(folder, name)
            else:
                ignored.append(path)
    return Selection(files, ignored)


def _excluded(path: str, excludes: Sequence[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in excludes)


def check_project(selection: Selection, entry: str, rules: Rules | None = None) -> Report:
    rules = rules or load_rules()
    findings: list[Finding] = []
    try:
        uploaded = check_upload(
            ((path, file.stat().st_size) for path, file in selection.files.items()), entry
        )
    except UploadError as error:
        findings.append(Finding(error.path or entry, None, UPLOAD, str(error)))
        sources = [path for path in selection.files if path.endswith(".py")]
        sources = [path for path in sources if not path.startswith(f"{DATA_DIR}/")]
    else:
        sources = [file.path for file in uploaded if file.kind == "source"]
    report = analyze({path: selection.files[path].read_bytes() for path in sources}, rules)
    return make_report(rules.ruleset, [*findings, *report.findings], rules.max_findings)
