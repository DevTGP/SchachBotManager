"""Case modules, one per vector file. Each defines FILE (path below testvectors/ without .json),
DESCRIPTION and CASES."""

from testvector_gen.cases import (
    api_board,
    api_board_moves,
    api_board_query,
    api_board_raw,
    api_board_state,
    api_move,
    fen,
    hash,
    rules,
    san,
    uci,
)

MODULES = (
    fen,
    uci,
    san,
    hash,
    rules,
    api_move,
    api_board,
    api_board_query,
    api_board_moves,
    api_board_state,
    api_board_raw,
)
