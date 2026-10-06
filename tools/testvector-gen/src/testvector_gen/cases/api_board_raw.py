"""Board functions for raw access as bitboards and arrays (spec/api/board_raw.json)."""

from testvector_gen.case import Case, Raises, square
from testvector_gen.codes import BLACK, NO_SQUARE, WHITE
from testvector_gen.errors import INVALID_ARGUMENT
from testvector_gen.position import setup

FILE = "api/board_raw"
DESCRIPTION = "Board functions for raw access as bitboards and arrays, with each declared error."

PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING = range(6)
KIWIPETE = setup("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")
CHECK = setup(moves="e2e4 f7f6 d1h5")
DOUBLE_CHECK = setup("4k3/8/5N2/8/8/8/8/4RK2 b - - 0 1")
PINS = setup("4k3/4r3/8/8/1b6/8/3NR3/4K3 w - - 0 1")


def _invalid(id: str, function: str, args: tuple) -> Case:
    return Case(id, function, args, board=setup(), expect=Raises(INVALID_ARGUMENT))


CASES = [
    Case(
        "bitboard.white_pawns",
        "Board.bitboard",
        (WHITE, PAWN),
        board=setup(),
        expect="0x000000000000ff00",
    ),
    Case(
        "bitboard.black_king",
        "Board.bitboard",
        (BLACK, KING),
        board=setup(),
        expect="0x1000000000000000",
    ),
    Case("bitboard.kiwipete_bishops", "Board.bitboard", (BLACK, BISHOP), board=KIWIPETE),
    _invalid("bitboard.color_2", "Board.bitboard", (2, PAWN)),
    _invalid("bitboard.piece_type_6", "Board.bitboard", (WHITE, 6)),
    Case("bitboards.start", "Board.bitboards", board=setup()),
    Case("bitboards.kiwipete", "Board.bitboards", board=KIWIPETE),
    Case("squares.start", "Board.squares", board=setup()),
    Case("squares.kiwipete", "Board.squares", board=KIWIPETE),
    Case("occupied.start", "Board.occupied", board=setup(), expect="0xffff00000000ffff"),
    Case("occupied.kiwipete", "Board.occupied", board=KIWIPETE),
    Case(
        "occupied_by.white",
        "Board.occupied_by",
        (WHITE,),
        board=setup(),
        expect="0x000000000000ffff",
    ),
    Case("occupied_by.black", "Board.occupied_by", (BLACK,), board=KIWIPETE),
    _invalid("occupied_by.color_2", "Board.occupied_by", (2,)),
    Case("piece_count.white_pawns", "Board.piece_count", (WHITE, PAWN), board=setup(), expect=8),
    Case("piece_count.black_queens", "Board.piece_count", (BLACK, QUEEN), board=KIWIPETE, expect=1),
    _invalid("piece_count.color_2", "Board.piece_count", (2, PAWN)),
    _invalid("piece_count.piece_type_6", "Board.piece_count", (WHITE, 6)),
    Case(
        "attacks_from.knight",
        "Board.attacks_from",
        (square("g1"),),
        board=setup(),
        note="Includes e2, a square of an own piece.",
    ),
    Case("attacks_from.blocked_rook", "Board.attacks_from", (square("a1"),), board=setup()),
    Case("attacks_from.queen", "Board.attacks_from", (square("f3"),), board=KIWIPETE),
    Case(
        "attacks_from.white_pawn",
        "Board.attacks_from",
        (square("e2"),),
        board=setup(),
        expect="0x0000000000280000",
        note="Diagonally only: d3 and f3.",
    ),
    Case(
        "attacks_from.black_pawn",
        "Board.attacks_from",
        (square("a7"),),
        board=setup(),
        expect="0x0000020000000000",
        note="Only b6 from the edge file.",
    ),
    Case(
        "attacks_from.pinned",
        "Board.attacks_from",
        (square("d2"),),
        board=PINS,
        note="Pins are ignored.",
    ),
    Case(
        "attacks_from.empty",
        "Board.attacks_from",
        (square("e4"),),
        board=setup(),
        expect="0x0000000000000000",
    ),
    _invalid("attacks_from.square_64", "Board.attacks_from", (NO_SQUARE,)),
    Case(
        "attackers_of.f3_white",
        "Board.attackers_of",
        (square("f3"), WHITE),
        board=setup(),
        note="Pawns on e2 and g2, knight on g1.",
    ),
    Case("attackers_of.d5_kiwipete", "Board.attackers_of", (square("d5"), BLACK), board=KIWIPETE),
    Case(
        "attackers_of.own_square",
        "Board.attackers_of",
        (square("e2"), WHITE),
        board=setup(),
        note="Squares of own pieces count.",
    ),
    _invalid("attackers_of.square_64", "Board.attackers_of", (NO_SQUARE, WHITE)),
    _invalid("attackers_of.color_2", "Board.attackers_of", (square("e4"), 2)),
    Case(
        "is_attacked.true", "Board.is_attacked", (square("f3"), WHITE), board=setup(), expect=True
    ),
    Case(
        "is_attacked.false", "Board.is_attacked", (square("e4"), WHITE), board=setup(), expect=False
    ),
    _invalid("is_attacked.square_64", "Board.is_attacked", (NO_SQUARE, WHITE)),
    _invalid("is_attacked.color_2", "Board.is_attacked", (square("e4"), 2)),
    Case("checkers.none", "Board.checkers", board=setup(), expect="0x0000000000000000"),
    Case("checkers.single", "Board.checkers", board=CHECK),
    Case("checkers.double", "Board.checkers", board=DOUBLE_CHECK, note="Knight f6 and rook e1."),
    Case(
        "pinned.white",
        "Board.pinned",
        (WHITE,),
        board=PINS,
        note="Knight d2 by the bishop on b4, rook e2 by the rook on e7.",
    ),
    Case(
        "pinned.black",
        "Board.pinned",
        (BLACK,),
        board=PINS,
        note="Rook e7 by the rook on e2; it may still move along the line.",
    ),
    Case("pinned.none", "Board.pinned", (WHITE,), board=setup(), expect="0x0000000000000000"),
    _invalid("pinned.color_2", "Board.pinned", (2,)),
]
