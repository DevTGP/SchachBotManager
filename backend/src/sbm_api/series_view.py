"""A series as the API shows it (schema Series, E155)."""

from sbm_api.match_view import match_summary

# Points of white and black per result; aborted and open games score nothing.
POINTS = {"1-0": (1.0, 0.0), "0-1": (0.0, 1.0), "1/2-1/2": (0.5, 0.5)}


def series_view(series_id: str, games: list[dict]) -> dict:
    """games are the summaries in order; bot a is white in the first of them."""
    first = games[0]
    a, b = first["white"], first["black"]
    points = {"a": 0.0, "b": 0.0}
    counted = 0
    for game in games:
        if game["result"] not in POINTS:
            continue
        counted += 1
        white_points, black_points = POINTS[game["result"]]
        # A bot against itself keeps its colours, so a stays white.
        a_is_white = game["white"]["bot_id"] == a["bot_id"]
        points["a"] += white_points if a_is_white else black_points
        points["b"] += black_points if a_is_white else white_points
    return {
        "id": series_id,
        "games": first["series"]["games"],
        "a": _bot(a, points["a"]),
        "b": _bot(b, points["b"]),
        "counted": counted,
        "matches": [match_summary(game) for game in games],
    }


def _bot(side: dict, points: float) -> dict:
    return {
        "bot_id": str(side["bot_id"]),
        "name": side["name"],
        "version": side.get("version"),
        "points": points,
    }
