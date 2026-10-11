"""The readiness of a league or tournament game with an account as the API shows it (schema
Readiness, E183)."""

from datetime import datetime

from sbm_store import competition_readiness, participants

from sbm_api.timestamps import optional_timestamp, timestamp


def readiness_view(readiness: dict | None, now: datetime) -> dict | None:
    """None until the game is released, and for all other matches."""
    if readiness is None:
        return None
    return {
        "released_at": timestamp(readiness["released_at"]),
        "deadline": timestamp(readiness["deadline"]),
        "started_at": optional_timestamp(readiness["started_at"]),
        **{
            color: competition_readiness.side_state(readiness[color], now)
            for color in participants.COLORS
        },
    }
