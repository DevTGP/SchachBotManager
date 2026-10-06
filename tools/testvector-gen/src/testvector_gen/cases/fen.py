"""Board.from_fen syntax and position rules, and the en passant square in Board.fen."""

from testvector_gen.case import Case, Raises
from testvector_gen.errors import INVALID_FEN
from testvector_gen.position import START_FEN, setup

FILE = "fen"
DESCRIPTION = (
    "FEN reading and writing: every syntax and position rule of Board.from_fen, and when "
    "Board.fen writes the en passant square."
)

PLACEMENT = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
KINGS = "4k3/8/8/8/8/8/8/4K3"


def _valid(id: str, fen: str, result: str | None = None, note: str | None = None) -> Case:
    return Case(id, "Board.from_fen", (fen,), note=note, expect=fen if result is None else result)


def _invalid(id: str, fen: str, note: str | None = None) -> Case:
    return Case(id, "Board.from_fen", (fen,), note=note, expect=Raises(INVALID_FEN))


SYNTAX = [
    _invalid("syntax.empty", ""),
    _invalid("syntax.five_fields", f"{PLACEMENT} w KQkq - 0"),
    _invalid("syntax.seven_fields", f"{START_FEN} 1"),
    _invalid("syntax.double_space", f"{PLACEMENT}  w KQkq - 0 1"),
    _invalid("syntax.leading_space", f" {START_FEN}"),
    _invalid("syntax.trailing_space", f"{START_FEN} "),
    _invalid("syntax.trailing_newline", f"{START_FEN}\n"),
    _invalid("syntax.tab", f"{PLACEMENT}\tw KQkq - 0 1"),
    _invalid("syntax.seven_ranks", "rnbqkbnr/pppppppp/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    _invalid("syntax.nine_ranks", "rnbqkbnr/pppppppp/8/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    _invalid("syntax.rank_too_long", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR1 w KQkq - 0 1"),
    _invalid("syntax.rank_too_short", "rnbqkbnr/pppppppp/7/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    _invalid("syntax.adjacent_digits", "rnbqkbnr/pppppppp/44/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    _invalid("syntax.digit_zero", "rnbqkbnr/pppppppp/08/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    _invalid("syntax.digit_nine", "rnbqkbnr/pppppppp/9/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    _invalid("syntax.unknown_letter", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNX w KQkq - 0 1"),
    _invalid("syntax.empty_rank", "rnbqkbnr/pppppppp//8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    _invalid("syntax.side_upper_case", f"{PLACEMENT} W KQkq - 0 1"),
    _invalid("syntax.side_word", f"{PLACEMENT} white KQkq - 0 1"),
    _invalid("syntax.castling_order", f"{PLACEMENT} w QKkq - 0 1"),
    _invalid("syntax.castling_repeated", f"{PLACEMENT} w KKkq - 0 1"),
    _invalid("syntax.castling_shredder", f"{PLACEMENT} w HAha - 0 1"),
    _invalid("syntax.castling_dash_and_letter", f"{PLACEMENT} w -K - 0 1"),
    _invalid("syntax.castling_empty", f"{PLACEMENT} w  - 0 1"),
    _invalid("syntax.en_passant_rank_4", f"{PLACEMENT} w KQkq e4 0 1"),
    _invalid("syntax.en_passant_upper_case", f"{PLACEMENT} w KQkq E6 0 1"),
    _invalid("syntax.en_passant_off_board", f"{PLACEMENT} w KQkq i6 0 1"),
    _invalid("syntax.halfmove_negative", f"{PLACEMENT} w KQkq - -1 1"),
    _invalid("syntax.halfmove_leading_zero", f"{PLACEMENT} w KQkq - 00 1"),
    _invalid("syntax.halfmove_plus", f"{PLACEMENT} w KQkq - +1 1"),
    _invalid("syntax.halfmove_above_i32", f"{PLACEMENT} w KQkq - 2147483648 1"),
    _invalid("syntax.halfmove_letter", f"{PLACEMENT} w KQkq - a 1"),
    _invalid("syntax.fullmove_zero", f"{PLACEMENT} w KQkq - 0 0"),
    _invalid("syntax.fullmove_leading_zero", f"{PLACEMENT} w KQkq - 0 01"),
    _invalid("syntax.fullmove_above_i32", f"{PLACEMENT} w KQkq - 0 2147483648"),
    _invalid("syntax.fullmove_non_ascii_digit", f"{PLACEMENT} w KQkq - 0 ١"),
]

POSITION = [
    _invalid("position.no_white_king", "4k3/8/8/8/8/8/8/8 w - - 0 1"),
    _invalid("position.two_black_kings", "3kk3/8/8/8/8/8/8/4K3 w - - 0 1"),
    _invalid("position.white_pawn_on_rank_8", "P3k3/8/8/8/8/8/8/4K3 w - - 0 1"),
    _invalid("position.black_pawn_on_rank_1", "4k3/8/8/8/8/8/8/p3K3 w - - 0 1"),
    _invalid(
        "position.seventeen_white_pieces",
        "rnbqkbnr/pppppppp/8/8/8/N7/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    ),
    _invalid(
        "position.side_not_to_move_in_check",
        "4k3/4R3/8/8/8/8/8/4K3 w - - 0 1",
        "Black is in check with White to move.",
    ),
    _invalid("position.castling_without_rook", f"{KINGS} w K - 0 1"),
    _invalid("position.castling_king_moved", "4k3/8/8/8/8/8/8/3K3R w K - 0 1"),
    _invalid("position.castling_black_rook_missing", "4k2r/8/8/8/8/8/8/4K3 w q - 0 1"),
    _invalid(
        "position.en_passant_wrong_rank_for_side",
        "4k3/8/8/8/3Pp3/8/8/4K3 w - d3 0 1",
        "With White to move the square must be on rank 6.",
    ),
    _invalid("position.en_passant_occupied", "4k3/8/3n4/3pP3/8/8/8/4K3 w - d6 0 1"),
    _invalid("position.en_passant_square_behind_occupied", "4k3/3n4/8/3pP3/8/8/8/4K3 w - d6 0 1"),
    _invalid("position.en_passant_without_pawn", "4k3/8/8/4P3/8/8/8/4K3 w - d6 0 1"),
    _invalid("position.en_passant_own_pawn", "4k3/8/8/3PP3/8/8/8/4K3 w - d6 0 1"),
]

VALID = [
    _valid("valid.start", START_FEN),
    _valid(
        "valid.kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    ),
    _valid("valid.castling_subset", "r3k2r/8/8/8/8/8/8/R3K2R b Kq - 3 20"),
    _valid("valid.max_counters", f"{KINGS} w - - 2147483647 2147483647"),
    _valid("valid.side_to_move_in_check", "4k3/8/8/8/8/8/4r3/4K3 w - - 0 1"),
    _valid("valid.sixteen_pieces", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b - - 0 1"),
    _valid(
        "valid.promoted_pieces",
        "4k3/8/8/8/8/8/QQQQ4/QQQQKQQQ w - - 0 1",
        note="Piece counts are not limited by type, only to 16 per side.",
    ),
    _valid("valid.en_passant_legal", "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1"),
    _valid("valid.en_passant_legal_black", "4k3/8/8/8/3Pp3/8/8/4K3 b - d3 0 1"),
    _valid(
        "valid.en_passant_without_capturing_pawn",
        "4k3/8/8/3p4/8/8/8/4K3 w - d6 0 1",
        "4k3/8/8/3p4/8/8/8/4K3 w - - 0 1",
        "Accepted and kept internally, but no capture is legal, so fen omits it.",
    ),
    _valid(
        "valid.en_passant_pinned",
        "8/8/8/KPp4r/8/8/8/7k w - c6 0 1",
        "8/8/8/KPp4r/8/8/8/7k w - - 0 1",
        "b5xc6 would expose the king on a5 to the rook on h5.",
    ),
]

WRITE = [
    Case(
        "write.after_double_push",
        "Board.fen",
        board=setup(moves="e2e4"),
        note="No black pawn can capture on e3.",
        expect="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
    ),
    Case(
        "write.after_double_push_capturable",
        "Board.fen",
        board=setup(moves="e2e4 d7d5 e4e5 f7f5"),
        expect="rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3",
    ),
    Case(
        "write.en_passant_after_other_move",
        "Board.fen",
        board=setup(moves="e2e4 d7d5 e4e5 f7f5 g1f3"),
        note="The right expires after one move.",
    ),
    Case("write.counters", "Board.fen", board=setup(moves="g1f3 g8f6 f3g1"), note="Halfmove 3."),
    Case("write.castling_lost", "Board.fen", board=setup(moves="e2e4 e7e5 e1e2 e8e7")),
]

CASES = SYNTAX + POSITION + VALID + WRITE
