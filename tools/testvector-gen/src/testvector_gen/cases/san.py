"""Board.san: piece letters, disambiguation, captures, castling, promotion, check and mate."""

from testvector_gen.case import Case, Raises, full, parsed
from testvector_gen.codes import NULL_MOVE, RESIGN
from testvector_gen.errors import ILLEGAL_MOVE
from testvector_gen.position import Setup, setup

FILE = "san"
DESCRIPTION = "Standard algebraic notation of legal moves with Board.san."

CASTLING = setup("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
PROMOTION = setup("r7/1P6/8/8/8/8/8/k3K3 w - - 0 1")


def _san(id: str, board: Setup, uci: str, text: str, note: str | None = None) -> Case:
    return Case(id, "Board.san", (full(board, uci),), board=board, note=note or uci, expect=text)


def _illegal(id: str, board: Setup, move: int, note: str) -> Case:
    return Case(id, "Board.san", (move,), board=board, note=note, expect=Raises(ILLEGAL_MOVE))


CASES = [
    _san("pawn_push", setup(), "e2e4", "e4"),
    _san("knight", setup(), "g1f3", "Nf3"),
    _san("black_piece", setup(moves="e2e4"), "b8c6", "Nc6"),
    _san("king", setup(moves="e2e4 e7e5"), "e1e2", "Ke2"),
    _san("piece_capture", setup(moves="e2e4 d7d5 g1f3 d5e4 f3e5 b8c6"), "e5c6", "Nxc6"),
    _san("pawn_capture", setup(moves="e2e4 d7d5"), "e4d5", "exd5"),
    _san("en_passant", setup(moves="e2e4 a7a6 e4e5 d7d5"), "e5d6", "exd6"),
    _san("disambiguate_file", setup("4k3/8/8/8/8/5N2/8/1N2K3 w - - 0 1"), "b1d2", "Nbd2"),
    _san("disambiguate_rank", setup("4k3/8/8/R7/8/8/8/R3K3 w - - 0 1"), "a1a3", "R1a3"),
    _san(
        "disambiguate_both",
        setup("4k3/8/8/8/8/Q7/8/Q1Q1K3 w - - 0 1"),
        "a1b2",
        "Qa1b2",
        "a1b2; the queens on a3 and c1 share the file and the rank.",
    ),
    _san(
        "disambiguate_file_over_rank",
        setup("4k3/8/8/8/8/8/8/R4RK1 w - - 0 1"),
        "a1d1",
        "Rad1",
    ),
    _san(
        "no_disambiguation_when_pinned",
        setup("4k3/8/8/8/1b6/8/3N4/4K1N1 w - - 0 1"),
        "g1f3",
        "Nf3",
        "g1f3; the knight on d2 also reaches f3 but is pinned.",
    ),
    _san("no_disambiguation_other_type", setup(moves="e2e4 e7e5"), "g1e2", "Ne2"),
    _san("king_castle", CASTLING, "e1g1", "O-O"),
    _san("queen_castle", CASTLING, "e1c1", "O-O-O"),
    _san("black_queen_castle", setup(CASTLING.fen, "a1b1"), "e8c8", "O-O-O"),
    _san("castle_with_check", setup("5k2/8/8/8/8/8/8/4K2R w K - 0 1"), "e1g1", "O-O+"),
    _san("promotion", PROMOTION, "b7b8q", "b8=Q"),
    _san("underpromotion", PROMOTION, "b7b8n", "b8=N"),
    _san("promotion_capture", PROMOTION, "b7a8r", "bxa8=R+"),
    _san("promotion_check", setup("4k3/1P6/8/8/8/8/8/4K3 w - - 0 1"), "b7b8q", "b8=Q+"),
    _san("check", setup(moves="e2e4 f7f6"), "d1h5", "Qh5+"),
    _san("checkmate", setup(moves="f2f3 e7e5 g2g4"), "d8h4", "Qh4#"),
    _san("en_passant_check", setup("8/8/8/3k4/4p3/8/3PK3/8 w - - 0 1", "d2d4"), "e4d3", "exd3+"),
    _illegal("illegal", setup(), parsed("e2e5"), "e2e5"),
    _illegal("null_move", setup(), NULL_MOVE, "NULL_MOVE"),
    _illegal("resign", setup(), RESIGN, "RESIGN"),
]
