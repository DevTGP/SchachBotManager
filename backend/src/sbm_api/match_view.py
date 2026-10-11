"""Matches as the API shows them (schemas MatchSummary, Match, Move)."""

from sbm_api import context
from sbm_api.readiness_view import readiness_view
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
        "white": side(match, "white"),
        "black": side(match, "black"),
        "discipline": discipline(match["discipline_snapshot"]),
        # Matches queued before E100 were never rated.
        "rated": match.get("rated", False),
        "result": match["result"],
        "termination": match["termination"],
        "ply_count": ply_count,
        "series": series_place(match.get("series")),
        "league": league_place(match.get("context")),
        "tournament": tournament_place(match.get("context")),
        "readiness": _readiness(match.get("readiness")),
        "created_at": timestamp(match["created_at"]),
        "started_at": optional_timestamp(match["started_at"]),
        "finished_at": optional_timestamp(match["finished_at"]),
    }


def _readiness(readiness: dict | None) -> dict | None:
    """Only a released game reads the clock, whether its accounts are present (E183)."""
    return None if readiness is None else readiness_view(readiness, context.now())


def series_place(series: dict | None) -> dict | None:
    """Where the match stands in its series (E155)."""
    if series is None:
        return None
    return {"id": str(series["id"]), "index": series["index"], "games": series["games"]}


def league_place(context: dict | None) -> dict | None:
    """Where a league game stands (E134); other matches have no league context."""
    if context is None or "league_id" not in context:
        return None
    return {
        "league_id": str(context["league_id"]),
        "league_name": context["league_name"],
        "season_id": str(context["season_id"]),
        "season_number": context["season_number"],
        "tier": context["tier"],
        "round": context["round"],
        "board": context["board"],
    }


def tournament_place(context: dict | None) -> dict | None:
    """Where a tournament game stands (E178)."""
    if context is None or "tournament_id" not in context:
        return None
    return {
        "tournament_id": str(context["tournament_id"]),
        "tournament_name": context["tournament_name"],
        "edition_id": str(context["edition_id"]),
        "edition_number": context["edition_number"],
        "format": context["format"],
        "round": context["round"],
        "board": context["board"],
        "phase": context["phase"],
        "game": context["game"],
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


def side(match: dict, color: str) -> dict:
    """The rating change is there once the runner has counted the match (E103).

    People and remote bots have no bot_id; their account and seat stay internal (E119).
    """
    side = match[color]
    rating = match.get("rating")
    bot_id = side["bot_id"]
    return {
        "kind": side["kind"],
        "bot_id": None if bot_id is None else str(bot_id),
        "name": side["name"],
        # Matches queued before E95 do not keep the version.
        "version": side.get("version"),
        "sdk": side["sdk"],
        "lang": side["lang"],
        "rating": (
            None
            if rating is None
            else {"before": rating[color]["before"], "after": rating[color]["after"]}
        ),
    }
