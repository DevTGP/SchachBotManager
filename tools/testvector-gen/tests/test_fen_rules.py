import chess
import pytest

from testvector_gen.errors import INVALID_FEN, ApiError
from testvector_gen.fen_rules import parse_fen


@pytest.mark.parametrize(
    "fen",
    [
        chess.STARTING_FEN,
        "4k3/8/8/8/8/8/8/4K3 b - - 2147483647 2147483647",
        "4k3/8/8/3p4/8/8/8/4K3 w - d6 0 1",
    ],
)
def test_valid(fen):
    assert parse_fen(fen).fen(en_passant="fen") == fen


@pytest.mark.parametrize(
    "fen",
    [
        "4k3/8/8/8/8/8/8/4K3 w - - 0",
        "4k3/8/8/8/8/8/8/4K3 w - - 0 0",
        "4k3/8/44/8/8/8/8/4K3 w - - 0 1",
        "r3k2r/8/8/8/8/8/8/R3K2R w kqKQ - 0 1",
        "4k3/8/8/8/8/8/8/4K3 w - - 2147483648 1",
        "8/8/8/8/8/8/8/4K3 w - - 0 1",
        "4k3/8/8/8/8/8/8/4K3 w Q - 0 1",
        "4k2R/8/8/8/8/8/8/4K3 w - - 0 1",
        "4k3/8/8/8/8/8/8/4K3 w - e6 0 1",
        "4k3/8/8/8/8/8/8/P3K3 w - - 0 1",
    ],
)
def test_invalid(fen):
    with pytest.raises(ApiError) as raised:
        parse_fen(fen)
    assert raised.value.name == INVALID_FEN


def test_en_passant_square_is_kept_when_no_capture_is_possible():
    board = parse_fen("4k3/8/8/3p4/8/8/8/4K3 w - d6 0 1")
    assert board.ep_square == chess.D6
    assert board.fen() == "4k3/8/8/3p4/8/8/8/4K3 w - - 0 1"
