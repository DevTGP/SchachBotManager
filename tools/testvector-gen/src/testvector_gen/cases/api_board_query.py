"""Board functions reading single properties (spec/api/board_query.json)."""

from testvector_gen.case import UNSET, Case, Raises, square
from testvector_gen.codes import BLACK, NO_PIECE, NO_SQUARE, WHITE
from testvector_gen.errors import INVALID_ARGUMENT
from testvector_gen.position import setup

FILE = "api/board_query"
DESCRIPTION = "Board functions reading single properties, with each declared error."

KIWIPETE = setup("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")
EN_PASSANT = setup(moves="e2e4 d7d5 e4e5 f7f5")


def _piece_at(name: str, expect: object = UNSET) -> Case:
    return Case(
        f"piece_at.{name}", "Board.piece_at", (square(name),), board=KIWIPETE, expect=expect
    )


CASES = [
    _piece_at("a1"),
    _piece_at("e2"),
    _piece_at("e8"),
    _piece_at("e7"),
    _piece_at("h3"),
    _piece_at("a3", NO_PIECE),
    Case(
        "piece_at.square_64",
        "Board.piece_at",
        (NO_SQUARE,),
        board=KIWIPETE,
        expect=Raises(INVALID_ARGUMENT),
    ),
    Case("side_to_move.white", "Board.side_to_move", board=setup(), expect=WHITE),
    Case("side_to_move.black", "Board.side_to_move", board=setup(moves="e2e4"), expect=BLACK),
    Case("castling_rights.all", "Board.castling_rights", board=setup(), expect=15),
    Case(
        "castling_rights.none",
        "Board.castling_rights",
        board=setup(moves="e2e4 e7e5 e1e2 e8e7"),
        expect=0,
    ),
    Case(
        "castling_rights.subset",
        "Board.castling_rights",
        board=setup("r3k2r/8/8/8/8/8/8/R3K2R w Kq - 0 1"),
        expect=9,
    ),
    Case(
        "castling_rights.not_possible_now",
        "Board.castling_rights",
        board=KIWIPETE,
        expect=15,
        note="Independent of whether castling is legal right now.",
    ),
    Case(
        "en_passant_square.legal", "Board.en_passant_square", board=EN_PASSANT, expect=square("f6")
    ),
    Case(
        "en_passant_square.not_capturable",
        "Board.en_passant_square",
        board=setup(moves="e2e4"),
        expect=NO_SQUARE,
    ),
    Case(
        "en_passant_square.pinned",
        "Board.en_passant_square",
        board=setup("8/8/8/KPp4r/8/8/8/7k w - c6 0 1"),
        expect=NO_SQUARE,
    ),
    Case("en_passant_square.none", "Board.en_passant_square", board=setup(), expect=NO_SQUARE),
    Case("halfmove_clock.start", "Board.halfmove_clock", board=setup(), expect=0),
    Case(
        "halfmove_clock.played",
        "Board.halfmove_clock",
        board=setup(moves="g1f3 g8f6 b1c3"),
        expect=3,
    ),
    Case("fullmove_number.start", "Board.fullmove_number", board=setup(), expect=1),
    Case(
        "fullmove_number.played",
        "Board.fullmove_number",
        board=setup(moves="g1f3 g8f6 b1c3"),
        expect=2,
    ),
    Case("king_square.white", "Board.king_square", (WHITE,), board=KIWIPETE, expect=square("e1")),
    Case(
        "king_square.black",
        "Board.king_square",
        (BLACK,),
        board=setup(moves="e2e4 e7e5 g1f3 e8e7"),
        expect=square("e7"),
    ),
    Case(
        "king_square.color_2",
        "Board.king_square",
        (2,),
        board=setup(),
        expect=Raises(INVALID_ARGUMENT),
    ),
]
