"""Board functions for raw access as bitboards and arrays (spec/api/board_raw.json)."""

import chess

from testvector_gen.codes import NO_PIECE, PIECE_TYPES, chess_color, chess_piece_type, piece_code
from testvector_gen.oracle import checks
from testvector_gen.oracle.call import Call, Handler
from testvector_gen.values import u64


def _pieces(board: chess.Board, color: int, piece_type: int) -> int:
    return int(board.pieces_mask(chess_piece_type(piece_type), chess_color(color)))


def _bitboard(call: Call) -> str:
    color, piece_type = call.args
    return u64(_pieces(call.require_board(), checks.color(color), checks.piece_type(piece_type)))


def _bitboards(call: Call) -> list[str]:
    board = call.require_board()
    return [u64(_pieces(board, *divmod(piece, PIECE_TYPES))) for piece in range(NO_PIECE)]


def _squares(call: Call) -> list[int]:
    board = call.require_board()
    return [piece_code(board.piece_at(square)) for square in chess.SQUARES]


def _occupied_by(call: Call) -> str:
    color = chess_color(checks.color(call.args[0]))
    return u64(call.require_board().occupied_co[color])


def _piece_count(call: Call) -> int:
    color, piece_type = call.args
    board = call.require_board()
    return chess.popcount(_pieces(board, checks.color(color), checks.piece_type(piece_type)))


def _attacks_from(call: Call) -> str:
    return u64(int(call.require_board().attacks_mask(checks.square(call.args[0]))))


def _attackers_of(call: Call) -> int:
    square, color = call.args
    board = call.require_board()
    return int(board.attackers_mask(chess_color(checks.color(color)), checks.square(square)))


def _pinned(call: Call) -> str:
    board = call.require_board()
    color = chess_color(checks.color(call.args[0]))
    own = chess.SquareSet(board.occupied_co[color])
    return u64(sum(chess.BB_SQUARES[square] for square in own if board.is_pinned(color, square)))


HANDLERS: dict[str, Handler] = {
    "Board.bitboard": _bitboard,
    "Board.bitboards": _bitboards,
    "Board.squares": _squares,
    "Board.occupied": lambda call: u64(call.require_board().occupied),
    "Board.occupied_by": _occupied_by,
    "Board.piece_count": _piece_count,
    "Board.attacks_from": _attacks_from,
    "Board.attackers_of": lambda call: u64(_attackers_of(call)),
    "Board.is_attacked": lambda call: _attackers_of(call) != 0,
    "Board.checkers": lambda call: u64(int(call.require_board().checkers_mask())),
    "Board.pinned": _pinned,
}
