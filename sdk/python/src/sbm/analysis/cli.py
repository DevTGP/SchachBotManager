"""sbm-check: checks a bot folder against the rules of the server before the upload.

Exit codes: 0 no findings, 1 findings, 2 invalid arguments.
"""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from sbm.analysis.project import check_project, select_files
from sbm.analysis.upload import DEFAULT_ENTRY

EXIT_FINDINGS = 1
EXIT_USAGE = 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sbm-check",
        description=(
            "Checks a Python bot as the server does after an upload: allowed files, sizes, "
            "imports and forbidden names. The upload takes the .py files outside hidden folders "
            "and __pycache__, and the files directly in data/."
        ),
    )
    parser.add_argument("folder", nargs="?", default=".", help="the bot's folder (default .)")
    parser.add_argument(
        "--entry", default=DEFAULT_ENTRY, help=f"the main file (default {DEFAULT_ENTRY})"
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="GLOB",
        help="leaves out matching paths, e.g. 'tests/*'; can be given more than once",
    )
    parser.add_argument("--json", action="store_true", help="prints the report as JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    options = parser.parse_args(argv)
    root = Path(options.folder)
    if not root.is_dir():
        parser.error(f"{options.folder} is not a folder")
    selection = select_files(root, options.exclude)
    report = check_project(selection, options.entry)
    if options.json:
        print(json.dumps(report.to_json(), indent=2))
    else:
        if selection.ignored:
            print(f"ignored: {', '.join(selection.ignored)}", file=sys.stderr)
        for finding in report.findings:
            print(finding.text())
        if report.truncated:
            print("… more findings not shown")
        count = len(selection.files)
        if report.ok:
            print(f"sbm-check: OK, {count} files checked ({report.ruleset})")
        else:
            print(f"sbm-check: {len(report.findings)} problems in {count} files ({report.ruleset})")
    return 0 if report.ok else EXIT_FINDINGS
