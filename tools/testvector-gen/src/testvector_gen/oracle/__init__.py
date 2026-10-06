"""Expected outcome of each Board and Move function, computed with python-chess.

Each module mirrors one file of spec/api/ and maps "Owner.name" to a handler.
"""

from testvector_gen.oracle import board, board_moves, board_query, board_raw, board_state, move
from testvector_gen.oracle.call import Handler

HANDLERS: dict[str, Handler] = {
    **move.HANDLERS,
    **board.HANDLERS,
    **board_query.HANDLERS,
    **board_moves.HANDLERS,
    **board_state.HANDLERS,
    **board_raw.HANDLERS,
}
