"""Every Board and Move call vector of spec/testvectors/ against the binding (E55)."""

import pytest
import spec_files
import vector_codec

import sbm

FUNCTIONS = spec_files.core_functions()
VECTORS = spec_files.call_vectors()


def setup_board(board: dict) -> sbm.Board:
    result = sbm.Board.from_fen(board["fen"])
    for uci in board["moves"]:
        if uci == "0000":
            result.make_null_move()
        else:
            result.make_move(result.parse_move(uci))
    return result


def call(vector: dict, board: sbm.Board | None):
    function = FUNCTIONS[vector["function"]]
    args = [
        vector_codec.decode(value, param["type"])
        for value, param in zip(vector["args"], function["params"], strict=True)
    ]
    owner = getattr(sbm, function["owner"])
    if function["kind"] == "constructor":
        return owner(*args)
    if function["kind"] == "static":
        return getattr(owner, function["name"])(*args)
    target = board if function["owner"] == "Board" else sbm.Move.from_value(vector["move"])
    return getattr(target, function["name"])(*args)


def test_vectors_found():
    assert len(VECTORS) > 500


@pytest.mark.parametrize("vector", VECTORS, ids=[vector["id"] for vector in VECTORS])
def test_call_vector(vector):
    function = FUNCTIONS[vector["function"]]
    board = setup_board(vector["board"]) if "board" in vector else None
    if "error" in vector:
        error = getattr(sbm, vector["error"] + "Error")
        with pytest.raises(error) as raised:
            call(vector, board)
        assert type(raised.value) is error
    else:
        result = call(vector, board)
        returns = function.get("returns", {}).get("type")
        actual = vector_codec.encode(result, returns) if returns else result
        if "result_contains" in vector:
            assert vector["result_contains"] in actual
        elif vector.get("unordered"):
            assert sorted(actual) == sorted(vector["result"])
        else:
            assert actual == vector["result"]
    if "board_after" in vector:
        assert board.fen() == vector["board_after"]
