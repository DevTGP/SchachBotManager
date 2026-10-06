"""Board functions reading single properties (spec/api/board_query.json)."""

from testvector_gen.codes import NO_SQUARE, castling_code, chess_color, color_code, piece_code
from testvector_gen.oracle import checks
from testvector_gen.oracle.call import Call, Handler
from testvector_gen.position import legal_en_passant_square


def _en_passant_square(call: Call) -> int:
    square = legal_en_passant_square(call.require_board())
    return NO_SQUARE if square is None else square


HANDLERS: dict[str, Handler] = {
    "Board.piece_at": lambda call: piece_code(
        call.require_board().piece_at(checks.square(call.args[0]))
    ),
    "Board.side_to_move": lambda call: color_code(call.require_board().turn),
    "Board.castling_rights": lambda call: castling_code(call.require_board()),
    "Board.en_passant_square": _en_passant_square,
    "Board.halfmove_clock": lambda call: call.require_board().halfmove_clock,
    "Board.fullmove_number": lambda call: call.require_board().fullmove_number,
    "Board.king_square": lambda call: call.require_board().king(
        chess_color(checks.color(call.args[0]))
    ),
}
