"""Chess rules: castling, en passant, promotion, end conditions and the effects of moves."""

from testvector_gen.case import Case, full, parsed
from testvector_gen.codes import BLACK, WHITE
from testvector_gen.position import Setup, setup

FILE = "rules"
DESCRIPTION = (
    "Chess rules beyond the move generator counts of perft: castling conditions, en passant, "
    "promotion, check, mate, stalemate, repetition, the fifty-move rule, insufficient material "
    "and the effects of making and taking back moves."
)

CASTLING = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
SHUFFLE = "g1f3 g8f6 f3g1 f6g8"


def _is(id: str, function: str, board: Setup, expect: bool, note: str | None = None) -> Case:
    return Case(id, function, board=board, note=note, expect=expect)


def _legal(id: str, board: Setup, uci: str, expect: bool, note: str | None = None) -> Case:
    return Case(id, "Board.is_legal", (parsed(uci),), board=board, note=note or uci, expect=expect)


def _make(id: str, board: Setup, uci: str, note: str | None = None) -> Case:
    return Case(id, "Board.make_move", (full(board, uci),), board=board, note=note or uci)


CASTLING_RULES = [
    _legal("castling.allowed", setup(CASTLING), "e1g1", True),
    _legal(
        "castling.through_check",
        setup("4k3/8/8/8/8/8/5r2/R3K2R w KQ - 0 1"),
        "e1g1",
        False,
        "e1g1; the rook on f2 attacks f1.",
    ),
    _legal(
        "castling.into_check",
        setup("4k3/8/8/8/8/8/6r1/R3K2R w KQ - 0 1"),
        "e1g1",
        False,
        "e1g1; the rook on g2 attacks g1.",
    ),
    _legal(
        "castling.out_of_check",
        setup("4k3/8/8/8/8/8/4r3/R3K2R w KQ - 0 1"),
        "e1c1",
        False,
        "e1c1 while the rook on e2 gives check.",
    ),
    _legal(
        "castling.rook_square_attacked",
        setup("4k3/8/8/8/8/8/1r6/R3K2R w KQ - 0 1"),
        "e1c1",
        True,
        "e1c1; only b1 is attacked, which the king does not cross.",
    ),
    _legal(
        "castling.rook_attacked",
        setup("4k3/8/8/8/8/8/7r/R3K2R w KQ - 0 1"),
        "e1g1",
        True,
        "e1g1; the rook on h1 may be attacked.",
    ),
    _legal(
        "castling.blocked",
        setup("4k3/8/8/8/8/8/8/RN2K2R w KQ - 0 1"),
        "e1c1",
        False,
        "e1c1 with a knight on b1.",
    ),
    _legal(
        "castling.right_lost",
        setup(CASTLING, "h1h2 a8a7 h2h1 a7a8"),
        "e1g1",
        False,
        "e1g1 after the rook went to h2 and back.",
    ),
    _legal(
        "castling.other_side_kept",
        setup(CASTLING, "h1h2 a8a7 h2h1 a7a8"),
        "e1c1",
        True,
        "e1c1 after the rook on h1 went to h2 and back.",
    ),
    _make("castling.king_side_effect", setup(CASTLING), "e1g1"),
    _make("castling.queen_side_effect", setup(CASTLING, "a1b1"), "e8c8"),
    _make("castling.king_move_loses_both", setup(CASTLING), "e1d1"),
    _make("castling.rook_capture_loses_right", setup(CASTLING), "a1a8"),
]

EN_PASSANT_RULES = [
    _legal("en_passant.allowed", setup(moves="e2e4 a7a6 e4e5 d7d5"), "e5d6", True),
    _legal(
        "en_passant.expired",
        setup(moves="e2e4 a7a6 e4e5 d7d5 g1f3 a6a5"),
        "e5d6",
        False,
        "e5d6 one move too late.",
    ),
    _legal(
        "en_passant.horizontal_pin",
        setup("8/8/8/KPp4r/8/8/8/7k w - c6 0 1"),
        "b5c6",
        False,
        "b5c6 would expose the king on a5 to the rook on h5.",
    ),
    _legal(
        "en_passant.diagonal_pin",
        setup("8/8/8/1k6/2pP4/8/8/4KB2 b - d3 0 1"),
        "c4d3",
        True,
        "c4d3; the pawn on c4 is pinned by the bishop on f1 but stays on the diagonal.",
    ),
    _legal(
        "en_passant.removes_checker",
        setup("8/8/8/2k5/3Pp3/8/8/4K3 b - d3 0 1"),
        "e4d3",
        True,
        "e4d3 captures the pawn on d4 that gives check.",
    ),
    Case(
        "en_passant.legal_moves",
        "Board.legal_moves",
        board=setup("8/8/8/2k5/3Pp3/8/8/4K3 b - d3 0 1"),
    ),
    _make("en_passant.effect", setup(moves="e2e4 a7a6 e4e5 d7d5"), "e5d6"),
    _make("en_passant.double_push_effect", setup(moves="e2e4 d7d5 e4e5"), "f7f5"),
]

PROMOTION_RULES = [
    Case(
        "promotion.legal_moves",
        "Board.legal_moves",
        board=setup("1n2k3/P7/8/8/8/8/8/4K3 w - - 0 1"),
    ),
    Case(
        "promotion.legal_captures",
        "Board.legal_captures",
        board=setup("1n2k3/P7/8/8/8/8/8/4K3 w - - 0 1"),
    ),
    _make("promotion.effect", setup("1n2k3/P7/8/8/8/8/8/4K3 w - - 0 1"), "a7b8n"),
    _make("promotion.black_effect", setup("4k3/8/8/8/8/8/p7/4K3 b - - 0 1"), "a2a1q"),
]

END_RULES = [
    _is("end.checkmate", "Board.is_checkmate", setup(moves="f2f3 e7e5 g2g4 d8h4"), True),
    _is("end.checkmate_is_check", "Board.is_check", setup(moves="f2f3 e7e5 g2g4 d8h4"), True),
    _is("end.checkmate_game_over", "Board.is_game_over", setup(moves="f2f3 e7e5 g2g4 d8h4"), True),
    _is("end.checkmate_not_draw", "Board.is_draw", setup(moves="f2f3 e7e5 g2g4 d8h4"), False),
    Case(
        "end.checkmate_no_moves",
        "Board.legal_moves",
        board=setup(moves="f2f3 e7e5 g2g4 d8h4"),
        expect=[],
    ),
    _is(
        "end.smothered_mate", "Board.is_checkmate", setup("6rk/5Npp/8/8/8/8/8/4K3 b - - 0 1"), True
    ),
    _is("end.check_not_mate", "Board.is_checkmate", setup(moves="e2e4 f7f6 d1h5"), False),
    _is("end.stalemate", "Board.is_stalemate", setup("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"), True),
    _is(
        "end.stalemate_not_check", "Board.is_check", setup("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"), False
    ),
    _is("end.stalemate_draw", "Board.is_draw", setup("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"), True),
    _is(
        "end.stalemate_game_over",
        "Board.is_game_over",
        setup("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"),
        True,
    ),
    _is("end.start_not_over", "Board.is_game_over", setup(), False),
]

REPETITION_RULES = [
    Case("repetition.twice", "Board.is_repetition", (2,), board=setup(moves=SHUFFLE), expect=True),
    Case(
        "repetition.not_three_times",
        "Board.is_repetition",
        (3,),
        board=setup(moves=SHUFFLE),
        expect=False,
    ),
    Case(
        "repetition.three_times",
        "Board.is_repetition",
        (3,),
        board=setup(moves=f"{SHUFFLE} {SHUFFLE}"),
        expect=True,
    ),
    _is("repetition.draw", "Board.is_draw", setup(moves=f"{SHUFFLE} {SHUFFLE}"), True),
    _is("repetition.game_over", "Board.is_game_over", setup(moves=f"{SHUFFLE} {SHUFFLE}"), True),
    _is(
        "repetition.not_yet_draw", "Board.is_draw", setup(moves=f"{SHUFFLE} g1f3 g8f6 f3g1"), False
    ),
    Case("repetition.once", "Board.is_repetition", (1,), board=setup(), expect=True),
    Case(
        "repetition.side_to_move",
        "Board.is_repetition",
        (2,),
        board=setup(moves="g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1"),
        note="Black to move; the same pieces occurred before with Black to move once.",
        expect=True,
    ),
    Case(
        "repetition.castling_rights",
        "Board.is_repetition",
        (2,),
        board=setup(CASTLING, "e1f1 e8f8 f1e1 f8e8"),
        note="Same pieces, but the castling rights are gone.",
        expect=False,
    ),
    Case(
        "repetition.en_passant_not_legal",
        "Board.is_repetition",
        (2,),
        board=setup(moves="e2e4 g8f6 g1f3 f6g8 f3g1"),
        note="After e2e4 no black pawn could capture on e3, so the positions are equal.",
        expect=True,
    ),
    Case(
        "repetition.en_passant_legal",
        "Board.is_repetition",
        (2,),
        board=setup("4k3/8/8/8/3p4/8/4P3/4K1N1 w - - 0 1", "e2e4 e8d8 g1f3 d8e8 f3g1"),
        note="After e2e4 d4xe3 was legal, so that position differs from the later one.",
        expect=False,
    ),
    Case(
        "repetition.null_moves",
        "Board.is_repetition",
        (2,),
        board=setup(moves="g1f3 0000 f3g1 0000"),
        note="Positions before null moves count as well.",
        expect=True,
    ),
]

FIFTY_MOVE_RULES = [
    _is(
        "fifty.reached",
        "Board.is_fifty_move_rule",
        setup("4k3/8/8/8/8/8/8/R3K3 w - - 99 60", "a1a2"),
        True,
    ),
    _is("fifty.draw", "Board.is_draw", setup("4k3/8/8/8/8/8/8/R3K3 w - - 99 60", "a1a2"), True),
    _is(
        "fifty.not_yet",
        "Board.is_fifty_move_rule",
        setup("4k3/8/8/8/8/8/8/R3K3 w - - 99 60"),
        False,
    ),
    _is(
        "fifty.reset_by_capture",
        "Board.is_fifty_move_rule",
        setup("4k3/8/8/8/8/8/r7/R3K3 w - - 99 60", "a1a2"),
        False,
    ),
    _is(
        "fifty.reset_by_pawn",
        "Board.is_fifty_move_rule",
        setup("4k3/8/8/8/8/8/P7/4K3 w - - 99 60", "a2a3"),
        False,
    ),
    _is(
        "fifty.from_fen",
        "Board.is_fifty_move_rule",
        setup("4k3/8/8/8/8/8/8/R3K3 w - - 150 80"),
        True,
    ),
    _is(
        "fifty.mate_first",
        "Board.is_fifty_move_rule",
        setup("7k/8/6K1/8/8/8/8/R7 w - - 99 60", "a1a8"),
        False,
        "Checkmate with the hundredth half move.",
    ),
    _is(
        "fifty.mate_first_game_over",
        "Board.is_game_over",
        setup("7k/8/6K1/8/8/8/8/R7 w - - 99 60", "a1a8"),
        True,
    ),
    _is(
        "fifty.null_move_counts",
        "Board.is_fifty_move_rule",
        setup("4k3/8/8/8/8/8/8/R3K3 w - - 99 60", "0000"),
        True,
    ),
]


def _material(id: str, fen: str, color: int, expect: bool) -> Case:
    return Case(
        f"material.{id}",
        "Board.has_insufficient_material",
        (color,),
        board=setup(fen),
        expect=expect,
    )


MATERIAL_RULES = [
    _material("king", "4k3/8/8/8/8/8/8/4K3 w - - 0 1", WHITE, True),
    _material("knight", "4k3/8/8/8/8/8/8/4KN2 w - - 0 1", WHITE, True),
    _material("knight_against_queen", "4k3/8/8/8/3q4/8/8/4KN2 w - - 0 1", WHITE, True),
    _material("knight_against_rook", "4k3/8/8/8/3r4/8/8/4KN2 w - - 0 1", WHITE, False),
    _material("knight_against_pawn", "4k3/p7/8/8/8/8/8/4KN2 w - - 0 1", WHITE, False),
    _material("two_knights", "4k3/8/8/8/8/8/8/3NKN2 w - - 0 1", WHITE, False),
    _material("bishop", "4k3/8/8/8/8/8/8/4KB2 w - - 0 1", WHITE, True),
    _material("bishops_both_colors", "4k3/8/8/8/8/8/8/2B1KB2 w - - 0 1", WHITE, False),
    _material("bishops_light", "4k3/8/8/8/8/8/6B1/4KB2 w - - 0 1", WHITE, True),
    _material("bishop_against_bishop_same", "4kb2/8/8/8/8/8/8/2B1K3 w - - 0 1", WHITE, True),
    _material("bishop_against_bishop_other", "4kb2/8/8/8/8/8/8/4KB2 w - - 0 1", WHITE, False),
    _material("bishop_against_knight", "4k3/8/8/8/8/8/8/1n2KB2 w - - 0 1", WHITE, False),
    _material("bishop_against_pawn", "4k3/p7/8/8/8/8/8/4KB2 w - - 0 1", WHITE, False),
    _material("bishop_against_rook", "4k2r/8/8/8/8/8/8/4KB2 w - - 0 1", WHITE, True),
    _material("knight_and_bishop", "4k3/8/8/8/8/8/8/4KBN1 w - - 0 1", WHITE, False),
    _material("pawn", "4k3/8/8/8/8/8/P7/4K3 w - - 0 1", WHITE, False),
    _material("rook", "4k3/8/8/8/8/8/8/R3K3 w - - 0 1", WHITE, False),
    _material("black_queen", "3qk3/8/8/8/8/8/8/4KN2 w - - 0 1", BLACK, False),
    _material("black_king", "3qk3/8/8/8/8/8/8/4K3 w - - 0 1", WHITE, True),
    _is(
        "material.both",
        "Board.is_insufficient_material",
        setup("4kb2/8/8/8/8/8/8/2B1K3 w - - 0 1"),
        True,
    ),
    _is(
        "material.one_side",
        "Board.is_insufficient_material",
        setup("4k3/8/8/8/8/8/8/R3K3 w - - 0 1"),
        False,
    ),
    _is("material.draw", "Board.is_draw", setup("4k3/8/8/8/8/8/8/4KN2 w - - 0 1"), True),
]

MOVE_EFFECTS = [
    _make("effect.quiet", setup(), "g1f3"),
    _make("effect.black_increments_fullmove", setup(moves="g1f3"), "g8f6"),
    _make("effect.capture_resets_halfmove", setup(moves="g1f3 d7d5 b1c3 e7e5"), "f3e5"),
    Case(
        "effect.null_move",
        "Board.make_null_move",
        board=setup(moves="e2e4 d7d5 e4e5 f7f5"),
        note="Clears the legal en passant square f6.",
    ),
    Case(
        "effect.black_null_move",
        "Board.make_null_move",
        board=setup(moves="g1f3"),
        note="Increases the fullmove number.",
    ),
    Case(
        "effect.undo_restores_en_passant",
        "Board.undo_move",
        board=setup(moves="e2e4 d7d5 e4e5 f7f5 g1f3"),
    ),
    Case(
        "effect.undo_null_restores_en_passant",
        "Board.undo_null_move",
        board=setup(moves="e2e4 d7d5 e4e5 f7f5 0000"),
    ),
    Case("effect.undo_restores_castling", "Board.undo_move", board=setup(CASTLING, "e1g1")),
    Case("effect.undo_restores_capture", "Board.undo_move", board=setup(CASTLING, "a1a8")),
    Case(
        "effect.undo_promotion",
        "Board.undo_move",
        board=setup("1n2k3/P7/8/8/8/8/8/4K3 w - - 0 1", "a7b8q"),
    ),
    Case("effect.history", "Board.move_history", board=setup(CASTLING, "e1g1 0000 a1a8")),
]

CASES = (
    CASTLING_RULES
    + EN_PASSANT_RULES
    + PROMOTION_RULES
    + END_RULES
    + REPETITION_RULES
    + FIFTY_MOVE_RULES
    + MATERIAL_RULES
    + MOVE_EFFECTS
)
