"""Board functions for creating, copying and printing (spec/api/board.json)."""

from testvector_gen.case import Case, Raises
from testvector_gen.errors import INVALID_FEN
from testvector_gen.position import START_FEN, setup

FILE = "api/board"
DESCRIPTION = "Board functions for creating, copying and printing, with each declared error."

KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
PLAYED = setup(moves="e2e4 e7e5 g1f3 0000 f1c4")

CASES = [
    Case("create", "Board.create", expect=START_FEN),
    Case("from_fen.start", "Board.from_fen", (START_FEN,), expect=START_FEN),
    Case("from_fen.kiwipete", "Board.from_fen", (KIWIPETE,), expect=KIWIPETE),
    Case(
        "from_fen.invalid",
        "Board.from_fen",
        ("8/8/8/8/8/8/8/8 w - - 0 1",),
        expect=Raises(INVALID_FEN),
    ),
    Case("fen.start", "Board.fen", board=setup(), expect=START_FEN),
    Case("fen.played", "Board.fen", board=PLAYED),
    Case("copy.start", "Board.copy", board=setup(), expect=START_FEN),
    Case("copy.played", "Board.copy", board=PLAYED),
    Case("hash.start", "Board.hash", board=setup(), expect="0x463b96181691fc9c"),
    Case("hash.played", "Board.hash", board=PLAYED),
    Case("move_history.empty", "Board.move_history", board=setup(), expect=[]),
    Case(
        "move_history.played",
        "Board.move_history",
        board=PLAYED,
        note="e2e4 double push, e7e5 double push, g1f3, NULL_MOVE, f1c4.",
    ),
    Case(
        "move_history.from_fen",
        "Board.move_history",
        board=setup(KIWIPETE),
        expect=[],
        note="from_fen starts with an empty history.",
    ),
    Case("to_text.start", "Board.to_text", board=setup(), expect=START_FEN),
    Case("to_text.played", "Board.to_text", board=PLAYED),
]
