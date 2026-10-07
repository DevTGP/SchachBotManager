"""Matches in the states the runner leaves them in, written through the store."""

from datetime import UTC, datetime, timedelta

from bson import ObjectId
from sbm_store import matches
from sbm_store.discipline import Discipline

NOW = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
BLITZ = Discipline("Blitz", initial_time_ms=180_000, increment_ms=2_000)
SITE = "https://sbm.example"

OPENING = [
    ("e2e4", "e4", "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"),
    ("e7e5", "e5", "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"),
]


def start_with_opening(db, match_id: ObjectId, now: datetime) -> None:
    matches.start(db, match_id, now)
    for ply, (uci, san, fen) in enumerate(OPENING, start=1):
        info = {"depth": 3, "score_cp": 20} if ply == 1 else None
        move = {
            "ply": ply,
            "uci": uci,
            "san": san,
            "fen": fen,
            "spent_ms": 150,
            "clock_ms": 181_850,
            "info": info,
        }
        matches.append_move(db, match_id, move)


def finish_by_resignation(db, match_id: ObjectId, now: datetime) -> None:
    start_with_opening(db, match_id, now)
    matches.finish(
        db,
        match_id,
        sides={color: {"sdk": "python-0.1.0", "lang": "python"} for color in ("white", "black")},
        result="1-0",
        termination="resignation",
        detail="black resigned",
        now=now + timedelta(minutes=2),
    )
