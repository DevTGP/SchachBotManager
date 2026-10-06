"""Board functions for creating, copying and printing (spec/api/board.json)."""

import chess
import chess.polyglot

from testvector_gen.fen_rules import parse_fen
from testvector_gen.oracle.call import Handler
from testvector_gen.position import history_values
from testvector_gen.values import u64

HANDLERS: dict[str, Handler] = {
    "Board.create": lambda call: chess.Board().fen(),
    "Board.from_fen": lambda call: parse_fen(call.args[0]).fen(),
    "Board.fen": lambda call: call.require_board().fen(),
    "Board.copy": lambda call: call.require_board().copy().fen(),
    "Board.hash": lambda call: u64(chess.polyglot.zobrist_hash(call.require_board())),
    "Board.move_history": lambda call: history_values(call.require_board()),
    # The layout is not part of the API; vectors only require the FEN in the text.
    "Board.to_text": lambda call: call.require_board().fen(),
}
