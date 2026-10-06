"""Board functions for end conditions (spec/api/board_state.json).

The fifty-move rule and repetitions are computed here: python-chess requires a legal move for
its fifty-move rule, and counting positions directly keeps the rule of the spec visible.
"""

import chess

from testvector_gen.codes import chess_color
from testvector_gen.errors import INVALID_ARGUMENT, ApiError
from testvector_gen.oracle import checks
from testvector_gen.oracle.call import Call, Handler
from testvector_gen.position import earlier_boards, position_key

FIFTY_MOVE_PLIES = 100
THREEFOLD = 3


def repetitions(board: chess.Board) -> int:
    """How often the current position occurs in the history, counting itself."""
    key = position_key(board)
    return sum(position_key(earlier) == key for earlier in earlier_boards(board))


def is_fifty_move_rule(board: chess.Board) -> bool:
    return board.halfmove_clock >= FIFTY_MOVE_PLIES and not board.is_checkmate()


def is_draw(board: chess.Board) -> bool:
    return (
        board.is_stalemate()
        or repetitions(board) >= THREEFOLD
        or is_fifty_move_rule(board)
        or board.is_insufficient_material()
    )


def _is_repetition(call: Call) -> bool:
    (count,) = call.args
    if count < 1:
        raise ApiError(INVALID_ARGUMENT)
    return repetitions(call.require_board()) >= count


def _has_insufficient_material(call: Call) -> bool:
    color = chess_color(checks.color(call.args[0]))
    return call.require_board().has_insufficient_material(color)


def _is_game_over(call: Call) -> bool:
    board = call.require_board()
    return board.is_checkmate() or is_draw(board)


HANDLERS: dict[str, Handler] = {
    "Board.is_check": lambda call: call.require_board().is_check(),
    "Board.is_checkmate": lambda call: call.require_board().is_checkmate(),
    "Board.is_stalemate": lambda call: call.require_board().is_stalemate(),
    "Board.is_repetition": _is_repetition,
    "Board.is_fifty_move_rule": lambda call: is_fifty_move_rule(call.require_board()),
    "Board.is_insufficient_material": lambda call: call.require_board().is_insufficient_material(),
    "Board.has_insufficient_material": _has_insufficient_material,
    "Board.is_draw": lambda call: is_draw(call.require_board()),
    "Board.is_game_over": _is_game_over,
}
