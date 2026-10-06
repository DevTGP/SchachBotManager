"""Board.hash: the published Polyglot keys and the Polyglot en passant rule."""

from testvector_gen.case import Case
from testvector_gen.position import setup

FILE = "hash"
DESCRIPTION = (
    "Board.hash equals the Polyglot book key. The first vectors are the example keys published "
    "with the Polyglot book format."
)

# Moves from the start position and the key published for the resulting position.
PUBLISHED = [
    ("start", "", "0x463b96181691fc9c"),
    ("e4", "e2e4", "0x823c9b50fd114196"),
    ("e4_d5", "e2e4 d7d5", "0x0756b94461c50fb0"),
    ("e4_d5_e5", "e2e4 d7d5 e4e5", "0x662fafb965db29d4"),
    ("e4_d5_e5_f5", "e2e4 d7d5 e4e5 f7f5", "0x22a48b5a8e47ff78"),
    ("e4_d5_e5_f5_ke2", "e2e4 d7d5 e4e5 f7f5 e1e2", "0x652a607ca3f242c1"),
    ("e4_d5_e5_f5_ke2_kf7", "e2e4 d7d5 e4e5 f7f5 e1e2 e8f7", "0x00fdd303c946bdd9"),
    ("a4_b5_h4_b4_c4", "a2a4 b7b5 h2h4 b5b4 c2c4", "0x3c8123ea7b067637"),
    ("a4_b5_h4_b4_c4_bxc3_ra3", "a2a4 b7b5 h2h4 b5b4 c2c4 b4c3 a1a3", "0x5c3f9b829b279560"),
]

PINNED_EN_PASSANT = "8/8/8/KPp4r/8/8/8/7k w - {} 0 1"
UNCAPTURABLE_EN_PASSANT = "4k3/8/8/3p4/8/8/8/4K3 w - {} 0 1"

CASES = [
    Case(f"published.{name}", "Board.hash", board=setup(moves=moves), expect=key)
    for name, moves, key in PUBLISHED
] + [
    Case(
        "en_passant.pinned",
        "Board.hash",
        board=setup(PINNED_EN_PASSANT.format("c6")),
        note="The pawn on b5 stands next to c5, so the key includes file c although b5xc6 is "
        "illegal; differs from en_passant.pinned_without.",
    ),
    Case("en_passant.pinned_without", "Board.hash", board=setup(PINNED_EN_PASSANT.format("-"))),
    Case(
        "en_passant.no_capturing_pawn",
        "Board.hash",
        board=setup(UNCAPTURABLE_EN_PASSANT.format("d6")),
        note="No white pawn next to d5: equal to en_passant.no_capturing_pawn_without.",
    ),
    Case(
        "en_passant.no_capturing_pawn_without",
        "Board.hash",
        board=setup(UNCAPTURABLE_EN_PASSANT.format("-")),
    ),
    Case(
        "transposition",
        "Board.hash",
        board=setup(moves="g1f3 g8f6 b1c3 b8c6"),
        note="Equal to transposition_other.",
    ),
    Case("transposition_other", "Board.hash", board=setup(moves="b1c3 b8c6 g1f3 g8f6")),
    Case(
        "counters_ignored",
        "Board.hash",
        board=setup(moves="g1f3 g8f6 f3g1 f6g8"),
        note="Start position with halfmove 4 and fullmove 3; the counters are not part of the key.",
        expect=PUBLISHED[0][2],
    ),
    Case("null_move", "Board.hash", board=setup(moves="e2e4 0000")),
]
