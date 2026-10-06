"""Turns a case into a call vector of calls.schema.json by asking the oracle."""

from testvector_gen.case import UNSET, Case, Raises
from testvector_gen.errors import ApiError
from testvector_gen.oracle import HANDLERS
from testvector_gen.oracle.call import Call
from testvector_gen.position import build

UNORDERED = {"Board.legal_moves", "Board.legal_captures"}
CONTAINS = {"Board.to_text"}
MUTATING = {"Board.make_move", "Board.undo_move", "Board.make_null_move", "Board.undo_null_move"}


class CaseError(Exception):
    """A case whose computed outcome differs from its `expect`."""


def build_vector(case: Case, prefix: str) -> dict:
    vector: dict = {"id": f"{prefix}.{case.id}", "function": case.function}
    if case.note is not None:
        vector["note"] = case.note
    board = None
    if case.board is not None:
        vector["board"] = case.board.to_json()
        board = build(case.board)
    if case.move is not None:
        vector["move"] = case.move
    vector["args"] = list(case.args)

    try:
        outcome: object = HANDLERS[case.function](Call(board, case.move, case.args))
    except ApiError as error:
        outcome = Raises(error.name)
        vector["error"] = error.name
    else:
        key = "result_contains" if case.function in CONTAINS else "result"
        vector[key] = outcome
        if case.function in UNORDERED:
            vector["unordered"] = True
    if case.function in MUTATING and board is not None:
        vector["board_after"] = board.fen()

    if case.expect is not UNSET and case.expect != outcome:
        raise CaseError(f"{vector['id']}: expected {case.expect!r}, computed {outcome!r}")
    return vector
