import json
from pathlib import Path

import pytest

from spec_check.check import check_spec

REPO_SPEC = Path(__file__).resolve().parents[3] / "spec"
COPIED = (
    "api/api.schema.json",
    "protocol/v1/common.schema.json",
    "testvectors/calls.schema.json",
    "testvectors/perft.schema.json",
)
LANGUAGES = ("python", "cpp", "java", "csharp", "javascript")
FEN = "4k3/8/8/8/8/8/8/4K3 w - - 0 1"
BOARD = {"fen": FEN, "moves": []}


def api_file(module: str, **sections: object) -> dict:
    return {"$schema": "api.schema.json", "module": module, "description": "x", **sections}


def function(name: str, owner: str, kind: str = "method", **extra: object) -> dict:
    return {"name": name, "kind": kind, "owner": owner, "params": [], "description": "x", **extra}


def calls(name: str, *vectors: dict) -> dict:
    schema = "../" * name.count("/") + "calls.schema.json"
    return {"$schema": schema, "description": "x", "vectors": list(vectors)}


def call(id: str, name: str, *args: object, **extra: object) -> dict:
    return {"id": f"calls.{id}", "function": name, "args": list(args), **extra}


# One succeeding vector and one per declared error for every function of the small API.
COVERING = [
    call("create", "Board.from_fen", FEN, result=FEN),
    call("invalid", "Board.from_fen", "x", error="Bad"),
    call("side", "Board.side_to_move", board=BOARD, result=0),
    call("make", "Board.make_move", 5900, board=BOARD, result=None, board_after=FEN),
    call("illegal", "Board.make_move", 0, board=BOARD, error="Bad", board_after=FEN),
    call("moves", "Board.legal_moves", board=BOARD, result=[772], unordered=True),
    call("occupied", "Board.occupied", board=BOARD, result="0x1000000000000010"),
    call("uci", "Move.uci", move=5900, result="e2e4"),
]


@pytest.fixture
def spec(spec_root: Path, write_json):
    """Writes the real vector schemas and a small, consistent API; returns a writer for calls."""
    for relative in COPIED:
        write_json(relative, json.loads((REPO_SPEC / relative).read_text(encoding="utf-8")))
    write_json(
        "api/primitives.json",
        api_file(
            "primitives",
            primitives=[
                {"name": name, "description": "x", "languages": dict.fromkeys(LANGUAGES, "t")}
                for name in ("bool", "u8", "u16", "u64", "string")
            ],
        ),
    )
    write_json(
        "api/types.json",
        api_file(
            "types",
            types=[
                {"name": "Color", "kind": "alias", "base": "u8", "description": "x"},
                {"name": "Bitboard", "kind": "alias", "base": "u64", "description": "x"},
                {"name": "Move", "kind": "value", "base": "u16", "description": "x"},
                {"name": "Board", "kind": "class", "description": "x"},
            ],
        ),
    )
    write_json("api/errors.json", api_file("errors", errors=[{"name": "Bad", "description": "x"}]))
    write_json(
        "api/board.json",
        api_file(
            "board",
            functions=[
                function(
                    "from_fen",
                    "Board",
                    "static",
                    params=[{"name": "fen", "type": "string"}],
                    returns={"type": "Board"},
                    errors=["Bad"],
                ),
                function("side_to_move", "Board", returns={"type": "Color"}),
                function(
                    "make_move", "Board", params=[{"name": "move", "type": "Move"}], errors=["Bad"]
                ),
                function("legal_moves", "Board", returns={"type": "list<Move>"}),
                function("occupied", "Board", returns={"type": "Bitboard"}),
                function("uci", "Move", returns={"type": "string"}),
            ],
        ),
    )

    def write(*vectors: dict, name: str = "calls") -> Path:
        return write_json(f"testvectors/{name}.json", calls(name, *vectors))

    return write


def messages(spec_root: Path) -> list[str]:
    return [problem.message for problem in check_spec(spec_root)]


def test_covering_vectors_pass(spec_root: Path, spec):
    spec(*COVERING)
    assert messages(spec_root) == []


def test_without_testvectors_directory_nothing_is_required(spec_root: Path, spec):
    for path in (spec_root / "testvectors").iterdir():
        path.unlink()
    (spec_root / "testvectors").rmdir()
    assert messages(spec_root) == []


@pytest.mark.parametrize(
    ("vector", "message"),
    [
        (call("x", "Board.castle", board=BOARD, result=0), "no Board or Move function"),
        (call("x", "Board.side_to_move", result=0), "board missing for a method of Board"),
        (call("x", "Move.uci", board=BOARD, move=1, result="b1a1"), "board not allowed"),
        (call("x", "Board.from_fen", FEN, move=1, result=FEN), "move not allowed"),
        (call("x", "Move.uci", move=0x6000, result="a1a1"), "move is no valid Move"),
        (call("x", "Board.make_move", board=BOARD, result=None), "1 argument(s) expected"),
        (call("x", "Board.make_move", 0x7000, board=BOARD, result=None), "argument move"),
        (call("x", "Board.from_fen", 1, result=FEN), "argument fen does not fit string"),
        (call("x", "Board.side_to_move", board=BOARD, result=256), "result does not fit Color"),
        (call("x", "Board.side_to_move", board=BOARD, result=True), "result does not fit Color"),
        (call("x", "Board.make_move", 1, board=BOARD, result=0), "no return value"),
        (call("x", "Board.side_to_move", board=BOARD, result=None), "result does not fit"),
        (call("x", "Board.occupied", board=BOARD, result="0x10"), "result does not fit Bitboard"),
        (call("x", "Board.legal_moves", board=BOARD, result=[-1]), "result does not fit list"),
        (call("x", "Board.side_to_move", board=BOARD, result=0, unordered=True), "unordered"),
        (call("x", "Board.side_to_move", board=BOARD, result_contains="0"), "result_contains"),
        (call("x", "Board.side_to_move", board=BOARD, error="Bad"), "error not declared"),
    ],
)
def test_call_problems(spec_root: Path, spec, vector: dict, message: str):
    spec(*COVERING, vector)
    found = messages(spec_root)
    assert len(found) == 1
    assert message in found[0]
    assert found[0].startswith("calls.x: ")


def test_coverage(spec_root: Path, spec):
    spec(*(vector for vector in COVERING if vector["id"] not in ("calls.uci", "calls.illegal")))
    assert sorted(messages(spec_root)) == [
        "no succeeding test vector for Move.uci",
        "no test vector for Board.make_move raising Bad",
    ]


def test_ids_unique_across_files_and_prefixed(spec_root: Path, spec, write_json):
    spec(*COVERING)
    spec(call("uci", "Move.uci", move=5900, result="e2e4"), name="sub/other")
    write_json(
        "testvectors/perft.json",
        {
            "$schema": "perft.schema.json",
            "description": "x",
            "vectors": [{"id": "perft.start.d1", "fen": FEN, "depth": 1, "nodes": 5}],
        },
    )
    assert sorted(messages(spec_root)) == [
        "calls.uci: id must start with sub.other.",
        "duplicate id: calls.uci",
    ]


def test_files_must_name_a_vector_schema(spec_root: Path, spec, write_json):
    spec(*COVERING)
    write_json("testvectors/notes.json", {"vectors": []})
    assert messages(spec_root) == ["vector files must name calls.schema.json or perft.schema.json"]
