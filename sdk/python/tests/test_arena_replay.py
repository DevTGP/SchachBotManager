"""The start position from a recorded game."""

import pytest

from sbm import Board
from sbm.arena.pgn import GameInfo, to_pgn
from sbm.arena.replay import ReplayError, replay_fen
from sbm.referee import STANDARD_FEN, MatchRecord, MatchSettings, MoveRecord, Outcome, SideRecord

ITALIAN = "1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O Nf6 *"


def fen_after(ucis: list[str], start_fen: str = STANDARD_FEN) -> str:
    board = Board.from_fen(start_fen)
    for uci in ucis:
        board.make_move(board.parse_move(uci))
    return board.fen()


def test_all_moves_by_default():
    expected = fen_after(["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5", "e1g1", "g8f6"])
    assert replay_fen(ITALIAN) == expected


def test_some_moves():
    assert replay_fen(ITALIAN, plies=0) == STANDARD_FEN
    assert replay_fen(ITALIAN, plies=3) == fen_after(["e2e4", "e7e5", "g1f3"])


def test_second_game_from_a_fen():
    pgn = f'{ITALIAN}\n\n[FEN "4k3/8/8/8/8/8/4P3/4K3 b - - 0 40"]\n40... Kd8 41. e4 *'
    assert replay_fen(pgn, game_number=2, plies=1) == "3k4/8/8/8/8/8/4P3/4K3 w - - 1 41"


def test_lenient_san():
    pgn = "1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. 0-0!? Nf6?! 5. Ng5 d5 6. exd5 Nxd5 7. Nxf7+ *"
    ucis = ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5", "e1g1", "g8f6"]
    ucis += ["f3g5", "d7d5", "e4d5", "f6d5", "g5f7"]
    assert replay_fen(pgn) == fen_after(ucis)


def test_arena_pgn_round_trip():
    ucis = ["f2f3", "e7e5", "g2g4"]
    board, moves = Board(), []
    for ply, uci in enumerate(ucis, 1):
        move = board.parse_move(uci)
        san = board.san(move)
        board.make_move(move)
        moves.append(MoveRecord(ply, uci, san, board.fen(), 5, 60_000, None))
    outcome = Outcome("*", "aborted", None, "stopped")
    record = MatchRecord(STANDARD_FEN, SideRecord("a"), SideRecord("b"), moves, outcome)
    pgn = to_pgn(record, MatchSettings(initial_time_ms=1), GameInfo("e", "s", "d", 1))
    assert replay_fen(pgn) == board.fen()


@pytest.mark.parametrize(
    ("pgn", "game_number", "plies", "message"),
    [
        (ITALIAN, 2, None, "there is no game 2, the PGN has 1"),
        (ITALIAN, 1, 9, "game 1 has only 8 half-moves"),
        ("1. e4 e5 2. Ke3 *", 1, None, r"2\. Ke3 is not a legal move"),
        ("1. e4 e4 *", 1, None, r"1\.\.\. e4 is not a legal move"),
        ("1. f3 e5 2. g4 Qh4# 0-1", 1, None, "game 1 is over after 4 half-moves"),
        ('[FEN "8/8/8/8 w - - 0 1"]\n*', 1, None, "FEN tag"),
        ('[Variant "Chess960"]\n1. e4 *', 1, None, "variant 'Chess960'"),
    ],
)
def test_errors(pgn, game_number, plies, message):
    with pytest.raises(ReplayError, match=message):
        replay_fen(pgn, game_number, plies)
