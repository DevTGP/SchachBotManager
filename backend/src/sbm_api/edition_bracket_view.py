"""The bracket of a knockout edition as the API shows it (schemas Duel, DuelSide, DuelGame,
E176, E180).

A duel keeps every game it laid out; an aborted game is replaced by a later entry with the same
phase and number, and only the last one counts for the points. The game list shows all of them.
"""

from sbm_store import edition_games
from sbm_store.league_table import SCORES

from sbm_api.league_view import league_bot


def bracket_view(edition: dict, games: list[dict]) -> list[dict]:
    """games are the edition's matches (edition_games.of_edition)."""
    found = {game["_id"]: game for game in games}
    entries = {entry["bot_id"]: entry for entry in edition["participants"]}
    return [_duel(duel, found, entries) for duel in edition["duels"]]


def _duel(duel: dict, found: dict, entries: dict) -> dict:
    latest = {(entry["phase"], entry["game"]): entry for entry in duel["games"]}.values()
    winner = duel["winner"]
    return {
        "round": duel["round"],
        "slot": duel["slot"],
        "a": _side(duel["a"], latest, found),
        "b": _side(duel["b"], latest, found),
        "winner": None if winner is None else str(winner),
        "decided": duel["decided"],
        "decided_by": duel["decided_by"],
        "games": [
            _game(entry, found[entry["match_id"]], entries)
            for entry in duel["games"]
            if entry["match_id"] in found
        ],
    }


def _side(side: dict | None, latest, found: dict) -> dict | None:
    if side is None:
        return None
    return {
        "bot": league_bot(side),
        "seed": side["seed"],
        "points": _points(side["bot_id"], latest, found, edition_games.REGULAR),
        "tiebreak_points": _points(side["bot_id"], latest, found, edition_games.TIEBREAK),
    }


def _points(bot_id, latest, found: dict, phase: str) -> float:
    total = 0.0
    for entry in latest:
        match = found.get(entry["match_id"])
        if entry["phase"] != phase or match is None:
            continue
        white, black = SCORES.get(match["result"], (0.0, 0.0))
        if entry["white"] == bot_id:
            total += white
        elif entry["black"] == bot_id:
            total += black
    return total


def _game(entry: dict, match: dict, entries: dict) -> dict:
    return {
        "match_id": str(entry["match_id"]),
        "phase": entry["phase"],
        "game": entry["game"],
        "white": league_bot(entries[entry["white"]]),
        "black": league_bot(entries[entry["black"]]),
        "status": match["status"],
        "result": match.get("result"),
        "termination": match.get("termination"),
    }
