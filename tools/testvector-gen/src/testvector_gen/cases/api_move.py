"""Every Move function with its declared errors (spec/api/move.json)."""

from testvector_gen.case import Case, Raises, full, parsed, square
from testvector_gen.codes import (
    CAPTURE,
    DOUBLE_PUSH,
    EN_PASSANT,
    KING_CASTLE,
    NULL_MOVE,
    PROMOTION,
    PROMOTION_CAPTURE,
    QUEEN_CASTLE,
    QUIET,
    RESIGN,
    move_value,
)
from testvector_gen.errors import INVALID_ARGUMENT, INVALID_UCI
from testvector_gen.position import setup

FILE = "api/move"
DESCRIPTION = (
    "Every Move function with a success case and each declared error. Arguments stay within the "
    "range of their declared type; values outside it exist only in some languages and are tested "
    "by each binding itself."
)

E2E4 = full(setup(), "e2e4")
KING_CASTLE_MOVE = move_value(square("e1"), square("g1"), KING_CASTLE)
QUEEN_CASTLE_MOVE = move_value(square("e8"), square("c8"), QUEEN_CASTLE)
EN_PASSANT_MOVE = move_value(square("e5"), square("d6"), EN_PASSANT)
CAPTURE_MOVE = move_value(square("e4"), square("d5"), CAPTURE)
QUIET_MOVE = move_value(square("g1"), square("f3"), QUIET)
PROMOTION_MOVE = move_value(square("a7"), square("a8"), PROMOTION + 3)
PROMOTION_CAPTURE_MOVE = move_value(square("b2"), square("a1"), PROMOTION_CAPTURE)

# Move methods called on each of these values; the note names the move.
KINDS = [
    ("quiet", QUIET_MOVE, "g1f3 quiet"),
    ("double_push", E2E4, "e2e4 double push"),
    ("king_castle", KING_CASTLE_MOVE, "e1g1 king castle"),
    ("queen_castle", QUEEN_CASTLE_MOVE, "e8c8 queen castle"),
    ("capture", CAPTURE_MOVE, "e4d5 capture"),
    ("en_passant", EN_PASSANT_MOVE, "e5d6 en passant"),
    ("promotion", PROMOTION_MOVE, "a7a8q promotion"),
    ("promotion_capture", PROMOTION_CAPTURE_MOVE, "b2a1n promotion with capture"),
    ("null_move", NULL_MOVE, "NULL_MOVE"),
    ("resign", RESIGN, "RESIGN"),
]
METHODS = [
    "value",
    "from_square",
    "to_square",
    "flags",
    "promotion",
    "is_promotion",
    "is_capture",
    "is_castling",
    "is_en_passant",
]


def _create(id: str, from_square: int, to_square: int, flags: int, expect: object) -> Case:
    return Case(f"create.{id}", "Move.create", (from_square, to_square, flags), expect=expect)


def _invalid_value(id: str, value: int) -> Case:
    return Case(f"from_value.{id}", "Move.from_value", (value,), expect=Raises(INVALID_ARGUMENT))


CREATE = [
    _create("double_push", square("e2"), square("e4"), DOUBLE_PUSH, E2E4),
    _create("highest", 63, 63, 15, 0xFFFF),
    _create("lowest", 0, 0, 0, NULL_MOVE),
    _create("from_square_64", 64, 0, 0, Raises(INVALID_ARGUMENT)),
    _create("to_square_64", 0, 64, 0, Raises(INVALID_ARGUMENT)),
    _create("square_255", 255, 0, 0, Raises(INVALID_ARGUMENT)),
    _create("flags_6", square("e2"), square("e4"), 6, Raises(INVALID_ARGUMENT)),
    _create("flags_7", square("e2"), square("e4"), 7, Raises(INVALID_ARGUMENT)),
    _create("flags_16", square("e2"), square("e4"), 16, Raises(INVALID_ARGUMENT)),
    _create("flags_255", square("e2"), square("e4"), 255, Raises(INVALID_ARGUMENT)),
]

FROM_VALUE = [
    Case("from_value.e2e4", "Move.from_value", (E2E4,), expect=E2E4),
    Case("from_value.null_move", "Move.from_value", (NULL_MOVE,), expect=NULL_MOVE),
    Case("from_value.resign", "Move.from_value", (RESIGN,), expect=RESIGN),
    _invalid_value("flags_6", move_value(square("e2"), square("e4"), 6)),
    _invalid_value("flags_7", move_value(square("e2"), square("e4"), 7)),
]

PARSE = [
    Case("parse.e2e4", "Move.parse", ("e2e4",), expect=move_value(12, 28, QUIET)),
    Case("parse.promotion", "Move.parse", ("a7a8q",), expect=PROMOTION_MOVE),
    Case("parse.invalid", "Move.parse", ("e2e4x",), expect=Raises(INVALID_UCI)),
]

ACCESSORS = [
    Case(f"{method}.{kind}", f"Move.{method}", move=value, note=note)
    for method in METHODS
    for kind, value, note in KINDS
]

UCI = [
    Case("uci.double_push", "Move.uci", move=E2E4, expect="e2e4"),
    Case("uci.promotion_capture", "Move.uci", move=PROMOTION_CAPTURE_MOVE, expect="b2a1n"),
    Case("uci.parsed", "Move.uci", move=parsed("h7h8b"), expect="h7h8b"),
    Case("uci.null_move", "Move.uci", move=NULL_MOVE, expect=Raises(INVALID_ARGUMENT)),
    Case("uci.resign", "Move.uci", move=RESIGN, expect=Raises(INVALID_ARGUMENT)),
]

CASES = CREATE + FROM_VALUE + PARSE + ACCESSORS + UCI
