"""Board functions for end conditions (spec/api/board_state.json)."""

from testvector_gen.case import Case, Raises
from testvector_gen.codes import BLACK, WHITE
from testvector_gen.errors import INVALID_ARGUMENT
from testvector_gen.position import setup

FILE = "api/board_state"
DESCRIPTION = "Board functions for end conditions, with each declared error."

MATE = setup(moves="f2f3 e7e5 g2g4 d8h4")
CHECK = setup(moves="e2e4 f7f6 d1h5")
STALEMATE = setup("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
REPEATED = setup(moves="g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8")
FIFTY = setup("4k3/8/8/8/8/8/8/R3K3 w - - 100 80")
KINGS = setup("4k3/8/8/8/8/8/8/4K3 w - - 0 1")

FLAGS = [
    ("is_check", CHECK, True),
    ("is_check", setup(), False),
    ("is_checkmate", MATE, True),
    ("is_checkmate", CHECK, False),
    ("is_stalemate", STALEMATE, True),
    ("is_stalemate", MATE, False),
    ("is_fifty_move_rule", FIFTY, True),
    ("is_fifty_move_rule", setup(), False),
    ("is_insufficient_material", KINGS, True),
    ("is_insufficient_material", setup(), False),
    ("is_draw", REPEATED, True),
    ("is_draw", MATE, False),
    ("is_game_over", MATE, True),
    ("is_game_over", setup(), False),
]

CASES = [
    Case(f"{name}.{str(expect).lower()}", f"Board.{name}", board=board, expect=expect)
    for name, board, expect in FLAGS
] + [
    Case("is_repetition.three", "Board.is_repetition", (3,), board=REPEATED, expect=True),
    Case("is_repetition.four", "Board.is_repetition", (4,), board=REPEATED, expect=False),
    Case(
        "is_repetition.zero",
        "Board.is_repetition",
        (0,),
        board=setup(),
        expect=Raises(INVALID_ARGUMENT),
    ),
    Case(
        "is_repetition.negative",
        "Board.is_repetition",
        (-1,),
        board=setup(),
        expect=Raises(INVALID_ARGUMENT),
    ),
    Case(
        "has_insufficient_material.white_rook",
        "Board.has_insufficient_material",
        (WHITE,),
        board=setup("4k3/8/8/8/8/8/8/R3K3 w - - 0 1"),
        expect=False,
    ),
    Case(
        "has_insufficient_material.black_king",
        "Board.has_insufficient_material",
        (BLACK,),
        board=setup("4k3/8/8/8/8/8/8/R3K3 w - - 0 1"),
        expect=True,
    ),
    Case(
        "has_insufficient_material.color_2",
        "Board.has_insufficient_material",
        (2,),
        board=setup(),
        expect=Raises(INVALID_ARGUMENT),
    ),
]
