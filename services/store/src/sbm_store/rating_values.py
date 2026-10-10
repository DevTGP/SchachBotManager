"""The ratings a bot or an account holds: one per discipline and the overall one (E163).

A holder keeps in `ratings` one entry per discipline it played rated games in, keyed by the
discipline id as hex: value, games and seq of the last counted match there. The overall rating
is not stored: it is the mean over the disciplines weighted by their games, rounded half up.
"""

from bson import ObjectId

FIELD = "ratings"


def key(discipline_id: ObjectId) -> str:
    """The key of a discipline in `ratings`; field paths take it as `ratings.<key>`."""
    return str(discipline_id)


def in_discipline(holder: dict | None, discipline_id: ObjectId, start: int) -> dict:
    """value and games in one discipline; without rated games there it stands at start (E154)."""
    entry = _entries(holder).get(key(discipline_id))
    if entry is None:
        return {"value": start, "games": 0}
    return {"value": entry["value"], "games": entry["games"]}


def overall(holder: dict | None, start: int) -> dict:
    """The weighted mean of all disciplines, e.g. 3000 in 8 games and 2000 in 92 give 2080."""
    entries = [entry for entry in _entries(holder).values() if entry["games"] > 0]
    games = sum(entry["games"] for entry in entries)
    if games == 0:
        return {"value": start, "games": 0}
    weighted = sum(entry["value"] * entry["games"] for entry in entries)
    # Half up also below zero: floor((2w + g) / 2g).
    return {"value": (2 * weighted + games) // (2 * games), "games": games}


def _entries(holder: dict | None) -> dict:
    return (holder or {}).get(FIELD) or {}
