"""Board functions reading single properties (spec/api/board_query.json)."""

from testvector_gen.codes import (
    NO_SQUARE,
    castling_code,
    chess_color,
    chess_piece_type,
    color_code,
    piece_code,
)
from testvector_gen.oracle import checks
from testvector_gen.oracle.call import Call, Handler
from testvector_gen.position import legal_en_passant_square


def _en_passant_square(call: Call) -> int:
    square = legal_en_passant_square(call.require_board())
    return NO_SQUARE if square is None else square


def _pieces(call: Call) -> list[dict]:
    board = call.require_board()
    color = checks.color_or_none(call.args[0])
    piece_type = checks.piece_type_or_none(call.args[1])
    found = []
    for square, piece in sorted(board.piece_map().items()):
        if color is not None and piece.color != chess_color(color):
            continue
        if piece_type is not None and piece.piece_type != chess_piece_type(piece_type):
            continue
        found.append({"square": square, "piece": piece_code(piece)})
    return found


HANDLERS: dict[str, Handler] = {
    "Board.piece_at": lambda call: piece_code(
        call.require_board().piece_at(checks.square(call.args[0]))
    ),
    "Board.pieces": _pieces,
    "Board.side_to_move": lambda call: color_code(call.require_board().turn),
    "Board.castling_rights": lambda call: castling_code(call.require_board()),
    "Board.en_passant_square": _en_passant_square,
    "Board.halfmove_clock": lambda call: call.require_board().halfmove_clock,
    "Board.fullmove_number": lambda call: call.require_board().fullmove_number,
    "Board.king_square": lambda call: call.require_board().king(
        chess_color(checks.color(call.args[0]))
    ),
}
