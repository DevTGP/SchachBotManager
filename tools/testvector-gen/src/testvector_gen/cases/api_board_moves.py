"""Board functions for generating, checking, making and taking back moves (board_moves.json)."""

from testvector_gen.case import Case, Raises, full, parsed
from testvector_gen.codes import NULL_MOVE, RESIGN
from testvector_gen.errors import ILLEGAL_MOVE, INVALID_STATE, INVALID_UCI
from testvector_gen.position import setup

FILE = "api/board_moves"
DESCRIPTION = (
    "Board functions for generating, checking, making and taking back moves, with each declared "
    "error. Mutating functions give board_after, also after an error."
)

KIWIPETE = setup("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")
EN_PASSANT = setup(moves="e2e4 d7d5 e4e5 f7f5")
CHECK = setup(moves="e2e4 f7f6 d1h5")
MATE = setup(moves="f2f3 e7e5 g2g4 d8h4")


def _is_legal(id: str, board, move: int, expect: bool, note: str) -> Case:
    return Case(f"is_legal.{id}", "Board.is_legal", (move,), board=board, note=note, expect=expect)


LEGAL_MOVES = [
    Case("legal_moves.start", "Board.legal_moves", board=setup()),
    Case("legal_moves.kiwipete", "Board.legal_moves", board=KIWIPETE),
    Case("legal_moves.en_passant", "Board.legal_moves", board=EN_PASSANT),
    Case("legal_moves.check", "Board.legal_moves", board=CHECK),
    Case("legal_moves.checkmate", "Board.legal_moves", board=MATE, expect=[]),
    Case("legal_captures.start", "Board.legal_captures", board=setup(), expect=[]),
    Case("legal_captures.kiwipete", "Board.legal_captures", board=KIWIPETE),
    Case("legal_captures.en_passant", "Board.legal_captures", board=EN_PASSANT),
]

IS_LEGAL = [
    _is_legal("parsed", setup(), parsed("e2e4"), True, "e2e4 from Move.parse, flags 0"),
    _is_legal("complete", setup(), full(setup(), "e2e4"), True, "e2e4 with double push flag"),
    _is_legal("castling_parsed", KIWIPETE, parsed("e1g1"), True, "e1g1 from Move.parse"),
    _is_legal("en_passant_parsed", EN_PASSANT, parsed("e5f6"), True, "e5f6 from Move.parse"),
    _is_legal(
        "promotion_missing",
        setup("4k3/P7/8/8/8/8/8/4K3 w - - 0 1"),
        parsed("a7a8"),
        False,
        "a7a8 without promotion piece",
    ),
    _is_legal("illegal", setup(), parsed("e2e5"), False, "e2e5"),
    _is_legal("null_move", setup(), NULL_MOVE, False, "NULL_MOVE"),
    _is_legal("resign", setup(), RESIGN, False, "RESIGN"),
]

PARSE_MOVE = [
    Case(
        "parse_move.double_push",
        "Board.parse_move",
        ("e2e4",),
        board=setup(),
        expect=full(setup(), "e2e4"),
    ),
    Case("parse_move.en_passant", "Board.parse_move", ("e5f6",), board=EN_PASSANT),
    Case(
        "parse_move.invalid_uci",
        "Board.parse_move",
        ("e2e4x",),
        board=setup(),
        expect=Raises(INVALID_UCI),
    ),
    Case(
        "parse_move.illegal",
        "Board.parse_move",
        ("e2e5",),
        board=setup(),
        expect=Raises(ILLEGAL_MOVE),
    ),
]

SAN = [
    Case(
        "san.knight",
        "Board.san",
        (full(setup(), "g1f3"),),
        board=setup(),
        note="g1f3",
        expect="Nf3",
    ),
    Case(
        "san.illegal",
        "Board.san",
        (parsed("e2e5"),),
        board=setup(),
        note="e2e5",
        expect=Raises(ILLEGAL_MOVE),
    ),
]

MAKE_MOVE = [
    Case(
        "make_move.complete",
        "Board.make_move",
        (full(setup(), "e2e4"),),
        board=setup(),
        note="e2e4 with double push flag",
    ),
    Case(
        "make_move.parsed",
        "Board.make_move",
        (parsed("e2e4"),),
        board=setup(),
        note="e2e4 from Move.parse; the board completes the flags",
    ),
    Case(
        "make_move.castling_parsed",
        "Board.make_move",
        (parsed("e1g1"),),
        board=KIWIPETE,
        note="e1g1 from Move.parse",
    ),
    Case(
        "make_move.illegal",
        "Board.make_move",
        (parsed("e2e5"),),
        board=setup(moves="g1f3 g8f6"),
        note="e2e5; the board stays unchanged",
        expect=Raises(ILLEGAL_MOVE),
    ),
    Case(
        "make_move.null_move",
        "Board.make_move",
        (NULL_MOVE,),
        board=setup(),
        note="NULL_MOVE is never legal; make_null_move passes the turn",
        expect=Raises(ILLEGAL_MOVE),
    ),
    Case(
        "make_move.resign",
        "Board.make_move",
        (RESIGN,),
        board=setup(),
        note="RESIGN",
        expect=Raises(ILLEGAL_MOVE),
    ),
    Case(
        "make_move.checkmated",
        "Board.make_move",
        (parsed("e1f2"),),
        board=MATE,
        note="e1f2",
        expect=Raises(ILLEGAL_MOVE),
    ),
]

UNDO = [
    Case("undo_move.last", "Board.undo_move", board=setup(moves="e2e4 e7e5"), expect=None),
    Case("undo_move.empty", "Board.undo_move", board=setup(), expect=Raises(INVALID_STATE)),
    Case(
        "undo_move.after_null_move",
        "Board.undo_move",
        board=setup(moves="e2e4 0000"),
        expect=Raises(INVALID_STATE),
    ),
    Case(
        "undo_move.from_fen",
        "Board.undo_move",
        board=KIWIPETE,
        expect=Raises(INVALID_STATE),
        note="from_fen starts with an empty history.",
    ),
    Case("make_null_move.white", "Board.make_null_move", board=setup(), expect=None),
    Case("make_null_move.clears_en_passant", "Board.make_null_move", board=EN_PASSANT),
    Case(
        "make_null_move.in_check", "Board.make_null_move", board=CHECK, expect=Raises(INVALID_STATE)
    ),
    Case(
        "undo_null_move.last", "Board.undo_null_move", board=setup(moves="e2e4 0000"), expect=None
    ),
    Case(
        "undo_null_move.empty", "Board.undo_null_move", board=setup(), expect=Raises(INVALID_STATE)
    ),
    Case(
        "undo_null_move.after_move",
        "Board.undo_null_move",
        board=setup(moves="0000 e7e5"),
        expect=Raises(INVALID_STATE),
    ),
]

CASES = LEGAL_MOVES + IS_LEGAL + PARSE_MOVE + SAN + MAKE_MOVE + UNDO
