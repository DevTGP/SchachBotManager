"""Finished games as PGN."""

from sbm import Board
from sbm.arena.pgn import LINE_WIDTH, GameInfo, to_pgn
from sbm.referee import STANDARD_FEN, MatchRecord, MatchSettings, MoveRecord, Outcome, SideRecord

GAME = GameInfo("sbm-arena", "local", "2026.10.06", 3)
SETTINGS = MatchSettings(initial_time_ms=60_000, increment_ms=1_000)


def record(ucis: list[str], outcome: Outcome, start_fen: str = STANDARD_FEN) -> MatchRecord:
    board = Board.from_fen(start_fen)
    moves = []
    for ply, uci in enumerate(ucis, 1):
        move = board.parse_move(uci)
        san = board.san(move)
        board.make_move(move)
        moves.append(MoveRecord(ply, uci, san, board.fen(), 5, 60_000, None))
    return MatchRecord(start_fen, SideRecord("alpha"), SideRecord('beta "2"'), moves, outcome)


def tags(pgn: str) -> dict[str, str]:
    lines = pgn.split("\n\n")[0].splitlines()
    return {line[1:].split(" ", 1)[0]: line.split(" ", 1)[1][1:-2] for line in lines}


def test_fools_mate():
    outcome = Outcome("0-1", "checkmate", 1, "checkmate")
    pgn = to_pgn(record(["f2f3", "e7e5", "g2g4", "d8h4"], outcome), SETTINGS, GAME)
    assert tags(pgn) == {
        "Event": "sbm-arena",
        "Site": "local",
        "Date": "2026.10.06",
        "Round": "3",
        "White": "alpha",
        "Black": 'beta \\"2\\"',
        "Result": "0-1",
        "TimeControl": "60+1",
        "Termination": "normal",
    }
    assert pgn.endswith("\n\n1. f3 e5 2. g4 Qh4# {checkmate: checkmate} 0-1\n")


def test_custom_start_with_black_to_move():
    fen = "4k3/8/8/8/8/8/4P3/4K3 b - - 0 40"
    outcome = Outcome("*", "aborted", None, "stopped")
    pgn = to_pgn(record(["e8d8", "e2e4", "d8e8"], outcome, fen), SETTINGS, GAME)
    assert tags(pgn)["SetUp"] == "1"
    assert tags(pgn)["FEN"] == fen
    assert tags(pgn)["Termination"] == "unterminated"
    assert "40... Kd8 41. e4 Ke8 {aborted: stopped} *" in pgn


def test_no_clock_and_terminations():
    settings = MatchSettings(initial_time_ms=1, clock=False)
    outcome = Outcome("1-0", "illegal_move", 0, "Black: illegal_move: e7e4 is not legal")
    pgn = to_pgn(record([], outcome), settings, GAME)
    assert tags(pgn)["TimeControl"] == "-"
    assert tags(pgn)["Termination"] == "rules infraction"
    assert pgn.endswith("{illegal_move: Black: illegal_move: e7e4 is not legal} 1-0\n")


def test_comment_cannot_break_out():
    outcome = Outcome("1-0", "crash", 0, "Black: left: } 0-1\n[Event")
    pgn = to_pgn(record([], outcome), SETTINGS, GAME)
    assert pgn.endswith("{crash: Black: left: ) 0-1 [Event} 1-0\n")
    assert tags(pgn)["Termination"] == "abandoned"


def test_lines_are_wrapped():
    outcome = Outcome("1/2-1/2", "threefold_repetition", None, "the position occurred three times")
    ucis = ["g1f3", "g8f6", "f3g1", "f6g8"] * 2
    pgn = to_pgn(record(ucis * 3, outcome), SETTINGS, GAME)
    movetext = pgn.split("\n\n")[1].splitlines()
    assert len(movetext) > 1
    assert all(len(line) <= LINE_WIDTH for line in movetext)
    assert " ".join(movetext).startswith("1. Nf3 Nf6 2. Ng1 Ng8 3. Nf3")
