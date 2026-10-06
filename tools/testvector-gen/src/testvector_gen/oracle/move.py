"""Move functions (spec/api/move.json)."""

import re

import chess

from testvector_gen.codes import (
    CAPTURE,
    EN_PASSANT,
    KING_CASTLE,
    MAX_FLAGS,
    NO_PIECE_TYPE,
    NULL_MOVE,
    PROMOTION,
    PROMOTION_CAPTURE,
    PROMOTION_LETTERS,
    QUEEN_CASTLE,
    RESIGN,
    UNUSED_FLAGS,
    move_parts,
    move_value,
)
from testvector_gen.errors import INVALID_ARGUMENT, INVALID_UCI, ApiError
from testvector_gen.oracle import checks
from testvector_gen.oracle.call import Call, Handler

UCI = re.compile(r"[a-h][1-8][a-h][1-8][nbrq]?")
U16_MAX = 0xFFFF


def parse_uci(text: str) -> int:
    """Move.parse: flags 8 to 11 for a promotion, otherwise 0."""
    if UCI.fullmatch(text) is None:
        raise ApiError(INVALID_UCI)
    flags = PROMOTION + PROMOTION_LETTERS.index(text[4]) if len(text) == 5 else 0
    return move_value(chess.parse_square(text[:2]), chess.parse_square(text[2:4]), flags)


def _create(call: Call) -> int:
    from_square, to_square, flags = call.args
    checks.square(from_square)
    checks.square(to_square)
    if not 0 <= flags <= MAX_FLAGS or flags in UNUSED_FLAGS:
        raise ApiError(INVALID_ARGUMENT)
    return move_value(from_square, to_square, flags)


def _from_value(call: Call) -> int:
    (value,) = call.args
    if not 0 <= value <= U16_MAX or move_parts(value)[2] in UNUSED_FLAGS:
        raise ApiError(INVALID_ARGUMENT)
    return value


def _flags(call: Call) -> int:
    return move_parts(call.require_move())[2]


def _promotion(call: Call) -> int:
    flags = _flags(call)
    return (flags & 3) + 1 if flags >= PROMOTION else NO_PIECE_TYPE


def _is_capture(call: Call) -> bool:
    flags = _flags(call)
    return flags in (CAPTURE, EN_PASSANT) or flags >= PROMOTION_CAPTURE


def _uci(call: Call) -> str:
    move = call.require_move()
    if move in (NULL_MOVE, RESIGN):
        raise ApiError(INVALID_ARGUMENT)
    from_square, to_square, flags = move_parts(move)
    suffix = PROMOTION_LETTERS[flags & 3] if flags >= PROMOTION else ""
    return chess.square_name(from_square) + chess.square_name(to_square) + suffix


HANDLERS: dict[str, Handler] = {
    "Move.create": _create,
    "Move.from_value": _from_value,
    "Move.parse": lambda call: parse_uci(call.args[0]),
    "Move.value": lambda call: call.require_move(),
    "Move.from_square": lambda call: move_parts(call.require_move())[0],
    "Move.to_square": lambda call: move_parts(call.require_move())[1],
    "Move.flags": _flags,
    "Move.promotion": _promotion,
    "Move.is_promotion": lambda call: _flags(call) >= PROMOTION,
    "Move.is_capture": _is_capture,
    "Move.is_castling": lambda call: _flags(call) in (KING_CASTLE, QUEEN_CASTLE),
    "Move.is_en_passant": lambda call: _flags(call) == EN_PASSANT,
    "Move.uci": _uci,
}
