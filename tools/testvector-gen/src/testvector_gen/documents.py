"""The content of every generated file below spec/testvectors/."""

from pathlib import PurePosixPath

from testvector_gen import perft
from testvector_gen.cases import MODULES
from testvector_gen.vectors import build_vector
from testvector_gen.writer import render

PERFT_DESCRIPTION = (
    "Leaf node counts of the legal move tree (perft) from the Chess Programming Wiki and the "
    "edge-case collection by Martin Sedlak. Vectors marked slow may be skipped in regular test "
    "runs."
)


def _schema(path: PurePosixPath, name: str) -> str:
    return "../" * (len(path.parts) - 1) + name


def documents() -> dict[str, str]:
    """Path relative to testvectors/ -> file content."""
    result = {"perft.json": render("perft.schema.json", PERFT_DESCRIPTION, perft.vectors())}
    for module in MODULES:
        path = PurePosixPath(f"{module.FILE}.json")
        prefix = module.FILE.replace("/", ".")
        vectors = [build_vector(case, prefix) for case in module.CASES]
        result[str(path)] = render(_schema(path, "calls.schema.json"), module.DESCRIPTION, vectors)
    return result
