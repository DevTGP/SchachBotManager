"""Board functions for generating, checking, making and taking back moves.

Moves are matched by from-square, to-square and promotion piece (spec/api/board_moves.json).
"""

import chess

from testvector_gen.codes import encode_move
from testvector_gen.errors import ILLEGAL_MOVE, INVALID_STATE, ApiError
from testvector_gen.oracle.call import Call, Handler
from testvector_gen.oracle.move import parse_uci
from testvector_gen.position import find_move


def _legal(board: chess.Board, value: int) -> chess.Move:
    move = find_move(board, value)
    if move is None:
        raise ApiError(ILLEGAL_MOVE)
    return move


def _legal_moves(call: Call) -> list[int]:
    board = call.require_board()
    return sorted(encode_move(board, move) for move in board.legal_moves)


def _legal_captures(call: Call) -> list[int]:
    board = call.require_board()
    return sorted(encode_move(board, move) for move in board.generate_legal_captures())


def _parse_move(call: Call) -> int:
    board = call.require_board()
    return encode_move(board, _legal(board, parse_uci(call.args[0])))


def _san(call: Call) -> str:
    board = call.require_board()
    return board.san(_legal(board, call.args[0]))


def _make_move(call: Call) -> None:
    board = call.require_board()
    board.push(_legal(board, call.args[0]))


def _last_is_null(board: chess.Board) -> bool | None:
    """None for an empty history."""
    return board.move_stack[-1] == chess.Move.null() if board.move_stack else None


def _undo_move(call: Call) -> None:
    board = call.require_board()
    if _last_is_null(board) is not False:
        raise ApiError(INVALID_STATE)
    board.pop()


def _make_null_move(call: Call) -> None:
    board = call.require_board()
    if board.is_check():
        raise ApiError(INVALID_STATE)
    board.push(chess.Move.null())


def _undo_null_move(call: Call) -> None:
    board = call.require_board()
    if _last_is_null(board) is not True:
        raise ApiError(INVALID_STATE)
    board.pop()


HANDLERS: dict[str, Handler] = {
    "Board.legal_moves": _legal_moves,
    "Board.legal_captures": _legal_captures,
    "Board.is_legal": lambda call: find_move(call.require_board(), call.args[0]) is not None,
    "Board.parse_move": _parse_move,
    "Board.san": _san,
    "Board.make_move": _make_move,
    "Board.undo_move": _undo_move,
    "Board.make_null_move": _make_null_move,
    "Board.undo_null_move": _undo_null_move,
}
