"""UCI notation: Move.parse without a board, Move.uci and Board.parse_move."""

from testvector_gen.case import UNSET, Case, Raises, full, parsed
from testvector_gen.codes import NULL_MOVE, RESIGN
from testvector_gen.errors import ILLEGAL_MOVE, INVALID_ARGUMENT, INVALID_UCI
from testvector_gen.position import Setup, setup

FILE = "uci"
DESCRIPTION = (
    "UCI notation: Move.parse without a board, Move.uci for every kind of move and "
    "Board.parse_move, which completes the flags."
)

CASTLING = setup("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
EN_PASSANT = setup(moves="e2e4 a7a6 e4e5 d7d5")
PROMOTION = setup("1n2k3/P7/8/8/8/8/8/4K3 w - - 0 1")


def _parse(id: str, text: str, note: str | None = None) -> Case:
    return Case(f"parse.{id}", "Move.parse", (text,), note=note)


def _parse_invalid(id: str, text: str) -> Case:
    return Case(f"parse.{id}", "Move.parse", (text,), expect=Raises(INVALID_UCI))


def _uci(id: str, move: int, text: str) -> Case:
    return Case(f"uci.{id}", "Move.uci", move=move, expect=text)


def _board(id: str, board: Setup, text: str, expect: object = UNSET) -> Case:
    return Case(f"board.{id}", "Board.parse_move", (text,), board=board, expect=expect)


PARSE = [
    _parse("quiet", "g1f3"),
    _parse("double_push", "e2e4", "Flags are 0: the double push is unknown without a board."),
    _parse("castling", "e1g1", "Castling is the king move."),
    _parse("corners", "a1h8"),
    _parse("promotion_knight", "a7a8n"),
    _parse("promotion_bishop", "b2b1b"),
    _parse("promotion_rook", "h7h8r"),
    _parse("promotion_queen", "e7e8q"),
    _parse("same_square", "e4e4", "Syntax only; the move is never legal."),
    _parse_invalid("empty", ""),
    _parse_invalid("null_move", "0000"),
    _parse_invalid("too_short", "e2e"),
    _parse_invalid("too_long", "e7e8qq"),
    _parse_invalid("upper_case_square", "E2E4"),
    _parse_invalid("upper_case_promotion", "e7e8Q"),
    _parse_invalid("king_promotion", "e7e8k"),
    _parse_invalid("pawn_promotion", "e7e8p"),
    _parse_invalid("file_out_of_range", "i2i4"),
    _parse_invalid("rank_zero", "e0e1"),
    _parse_invalid("rank_nine", "e8e9"),
    _parse_invalid("separator", "e2-e4"),
    _parse_invalid("trailing_space", "e2e4 "),
    _parse_invalid("trailing_newline", "e2e4\n"),
    _parse_invalid("san", "Nf3"),
]

TO_UCI = [
    _uci("quiet", full(setup(), "g1f3"), "g1f3"),
    _uci("double_push", full(setup(), "e2e4"), "e2e4"),
    _uci("king_castle", full(CASTLING, "e1g1"), "e1g1"),
    _uci("queen_castle", full(CASTLING, "e1c1"), "e1c1"),
    _uci("en_passant", full(EN_PASSANT, "e5d6"), "e5d6"),
    _uci("promotion", full(PROMOTION, "a7a8q"), "a7a8q"),
    _uci("promotion_capture", full(PROMOTION, "a7b8n"), "a7b8n"),
    _uci("parsed_promotion", parsed("h2h1r"), "h2h1r"),
    Case("uci.null_move", "Move.uci", move=NULL_MOVE, expect=Raises(INVALID_ARGUMENT)),
    Case("uci.resign", "Move.uci", move=RESIGN, expect=Raises(INVALID_ARGUMENT)),
]

BOARD = [
    _board("quiet", setup(), "g1f3"),
    _board("double_push", setup(), "e2e4"),
    _board("capture", setup(moves="e2e4 d7d5"), "e4d5"),
    _board("king_castle", CASTLING, "e1g1"),
    _board("queen_castle", CASTLING, "e1c1"),
    _board("black_castle", setup(CASTLING.fen, "a1b1"), "e8c8"),
    _board("en_passant", EN_PASSANT, "e5d6"),
    _board("promotion", PROMOTION, "a7a8r"),
    _board("promotion_capture", PROMOTION, "a7b8q"),
    _board("illegal", setup(), "e2e5", Raises(ILLEGAL_MOVE)),
    _board("wrong_side", setup(), "e7e5", Raises(ILLEGAL_MOVE)),
    _board("empty_square", setup(), "e3e4", Raises(ILLEGAL_MOVE)),
    _board("promotion_missing", PROMOTION, "a7a8", Raises(ILLEGAL_MOVE)),
    _board("promotion_not_allowed", setup(), "e2e4q", Raises(ILLEGAL_MOVE)),
    _board("castling_as_rook_capture", CASTLING, "e1h1", Raises(ILLEGAL_MOVE)),
    _board("null_move", setup(), "0000", Raises(INVALID_UCI)),
    _board("syntax_before_legality", setup(), "E2E4", Raises(INVALID_UCI)),
]

CASES = PARSE + TO_UCI + BOARD
