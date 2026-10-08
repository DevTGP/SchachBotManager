"""Matches as the API shows them (schemas MatchSummary, Match, Move)."""

from sbm_api.timestamps import optional_timestamp, timestamp

DISCIPLINE_FIELDS = (
    "name",
    "initial_time_ms",
    "increment_ms",
    "startup_ms",
    "tolerance_ms",
    "max_moves",
)
MOVE_FIELDS = ("ply", "uci", "san", "fen", "spent_ms", "clock_ms", "info")


def match_summary(match: dict) -> dict:
    """Takes a full match or one read with the summary projection (which counts the moves)."""
    ply_count = match["ply_count"] if "ply_count" in match else len(match["moves"])
    return {
        "id": str(match["_id"]),
        "type": match["type"],
        "status": match["status"],
        "white": side(match["white"]),
        "black": side(match["black"]),
        "discipline": discipline(match["discipline_snapshot"]),
        # Matches queued before E100 were never rated.
        "rated": match.get("rated", False),
        "result": match["result"],
        "termination": match["termination"],
        "ply_count": ply_count,
        "created_at": timestamp(match["created_at"]),
        "started_at": optional_timestamp(match["started_at"]),
        "finished_at": optional_timestamp(match["finished_at"]),
    }


def discipline(snapshot: dict) -> dict:
    """Matches queued before E100 have no discipline_id: they had free times."""
    discipline_id = snapshot.get("discipline_id")
    return {field: snapshot[field] for field in DISCIPLINE_FIELDS} | {
        "discipline_id": None if discipline_id is None else str(discipline_id)
    }


def match_detail(match: dict) -> dict:
    """termination_detail stays internal: for aborted matches it names infrastructure errors."""
    return match_summary(match) | {
        "start_fen": match["start_fen"],
        "moves": [{field: move[field] for field in MOVE_FIELDS} for move in match["moves"]],
    }


def side(side: dict) -> dict:
    return {
        "kind": side["kind"],
        "bot_id": str(side["bot_id"]),
        "name": side["name"],
        # Matches queued before E95 do not keep the version.
        "version": side.get("version"),
        "sdk": side["sdk"],
        "lang": side["lang"],
    }
