"""Command line entry point: `spec-check [root]`."""

import argparse
import sys
from pathlib import Path

from spec_check.check import check_spec

EXIT_OK = 0
EXIT_PROBLEMS = 1
EXIT_USAGE = 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="spec-check", description="Validate the JSON files below a spec directory."
    )
    parser.add_argument("root", nargs="?", default="spec", type=Path)
    args = parser.parse_args(argv)

    root = args.root.resolve()
    if not root.is_dir():
        print(f"spec-check: not a directory: {args.root}", file=sys.stderr)
        return EXIT_USAGE

    problems = check_spec(root)
    for problem in problems:
        print(f"{problem.path.relative_to(root).as_posix()}: {problem.message}")
    if problems:
        print(f"spec-check: {len(problems)} problem(s) found", file=sys.stderr)
        return EXIT_PROBLEMS
    print("spec-check: OK")
    return EXIT_OK
