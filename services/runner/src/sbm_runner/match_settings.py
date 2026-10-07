"""Referee settings from a stored match."""

from sbm.referee import MatchSettings


def match_settings(match: dict) -> MatchSettings:
    discipline = match["discipline_snapshot"]
    return MatchSettings(
        initial_time_ms=discipline["initial_time_ms"],
        increment_ms=discipline["increment_ms"],
        startup_ms=discipline["startup_ms"],
        tolerance_ms=discipline["tolerance_ms"],
        max_moves=discipline["max_moves"],
        start_fen=match["start_fen"],
        game_id=str(match["_id"]),
        discipline=discipline["name"],
    )
