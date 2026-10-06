import pytest

from testvector_gen.case import Case, Raises
from testvector_gen.position import setup
from testvector_gen.vectors import CaseError, build_vector


def test_result_vector_keys_in_order():
    vector = build_vector(Case("a", "Board.side_to_move", board=setup(), note="n"), "f")
    assert list(vector) == ["id", "function", "note", "board", "args", "result"]
    assert vector["id"] == "f.a"
    assert vector["result"] == 0


def test_error_of_mutating_function_keeps_board_after():
    vector = build_vector(Case("a", "Board.make_move", (0,), board=setup()), "f")
    assert vector["error"] == "IllegalMove"
    assert vector["board_after"] == setup().fen
    assert "result" not in vector


def test_unordered_and_contains():
    moves = build_vector(Case("a", "Board.legal_moves", board=setup()), "f")
    text = build_vector(Case("b", "Board.to_text", board=setup()), "f")
    assert moves["unordered"] is True
    assert len(moves["result"]) == 20
    assert text["result_contains"] == setup().fen


def test_move_method():
    vector = build_vector(Case("a", "Move.uci", move=5900), "f")
    assert vector["move"] == 5900
    assert vector["result"] == "e2e4"


def test_expect_mismatch_fails():
    with pytest.raises(CaseError):
        build_vector(Case("a", "Board.is_check", board=setup(), expect=True), "f")
    with pytest.raises(CaseError):
        build_vector(Case("b", "Board.is_check", board=setup(), expect=Raises("InvalidState")), "f")


def test_illegal_setup_fails():
    with pytest.raises(ValueError):
        build_vector(Case("a", "Board.fen", board=setup(moves="e2e5")), "f")
