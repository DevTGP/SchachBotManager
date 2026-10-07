"""A stored match as PGN, written like the arena's games (sbm.arena.pgn)."""

from sbm.arena.pgn import PGN_TERMINATIONS, game_text
from sbm.arena.time_control import format_time_control
from sbm.referee import STANDARD_FEN

EVENT = "SchachBotManager"
UNFINISHED = "*"


def match_pgn(match: dict, site: str) -> str:
    """A running or queued match ends with * and the Termination tag unterminated."""
    result = match["result"] or UNFINISHED
    termination = match["termination"]
    discipline = match["discipline_snapshot"]
    started = match["started_at"] or match["created_at"]
    tags = [
        ("Event", EVENT),
        ("Site", site),
        ("Date", started.strftime("%Y.%m.%d")),
        ("Round", "-"),
        ("White", match["white"]["name"]),
        ("Black", match["black"]["name"]),
        ("Result", result),
    ]
    if match["start_fen"] != STANDARD_FEN:
        tags += [("SetUp", "1"), ("FEN", match["start_fen"])]
    pgn_termination = PGN_TERMINATIONS.get(termination, "normal") if termination else "unterminated"
    tags += [
        (
            "TimeControl",
            format_time_control(discipline["initial_time_ms"], discipline["increment_ms"]),
        ),
        ("Termination", pgn_termination),
    ]
    sans = [move["san"] for move in match["moves"]]
    # Only the code: termination_detail may name infrastructure errors.
    return game_text(tags, match["start_fen"], sans, termination, result)
