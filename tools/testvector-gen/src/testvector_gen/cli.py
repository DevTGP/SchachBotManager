"""Command line: writes the vector files or checks that the checked-in files are current."""

import argparse
import sys
from pathlib import Path

from testvector_gen import perft
from testvector_gen.documents import documents

GENERATED_SUFFIX = ".json"
SCHEMA_SUFFIX = ".schema.json"


def _existing(directory: Path) -> set[str]:
    return {
        path.relative_to(directory).as_posix()
        for path in directory.rglob(f"*{GENERATED_SUFFIX}")
        if not path.name.endswith(SCHEMA_SUFFIX)
    }


def _read(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.is_file() else None


def check(directory: Path, expected: dict[str, str]) -> list[str]:
    problems = [
        f"{name}: {'missing' if _read(directory / name) is None else 'differs'}"
        for name, text in sorted(expected.items())
        if _read(directory / name) != text
    ]
    problems += [f"{name}: not generated" for name in sorted(_existing(directory) - set(expected))]
    return problems


def write(directory: Path, expected: dict[str, str]) -> None:
    for name, text in expected.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="testvector-gen", description="Generates the files below <spec>/testvectors/."
    )
    parser.add_argument("spec", nargs="?", default="spec", type=Path, help="spec directory")
    parser.add_argument(
        "--check", action="store_true", help="only report files that are not current"
    )
    parser.add_argument(
        "--perft",
        choices=("fast", "all"),
        help="recount perft vectors with python-chess: those without slow, or all",
    )
    args = parser.parse_args(argv)

    directory = args.spec / "testvectors"
    if not directory.is_dir():
        print(f"error: {directory} is not a directory", file=sys.stderr)
        return 2

    problems: list[str] = []
    expected = documents()
    if args.check:
        problems += check(directory, expected)
    else:
        write(directory, expected)
    if args.perft:
        problems += perft.verify(perft.SLOW_NODES if args.perft == "fast" else None)

    for problem in problems:
        print(problem)
    if problems:
        print(f"{len(problems)} problem(s)", file=sys.stderr)
        return 1
    return 0
