"""The games of a round robin or Swiss edition by rounds and boards (schema EditionRounds,
E180). Knockout editions keep their games in the bracket and show no rounds here."""

from sbm_api.league_view import league_bot


def rounds_view(edition: dict, games: list[dict]) -> dict:
    """games are the edition's matches (edition_games.of_edition)."""
    found = {game["_id"]: game for game in games}
    entries = {entry["bot_id"]: entry for entry in edition["participants"]}
    return {"rounds": [_round(planned, found, entries) for planned in edition["rounds"]]}


def _round(planned: dict, found: dict, entries: dict) -> dict:
    bye = planned["bye"]
    return {
        "round": planned["round"],
        "bye": None if bye is None else league_bot(entries[bye]),
        "games": [
            _game(pairing, found[pairing["match_id"]], entries)
            for pairing in planned["pairings"]
            if pairing["match_id"] in found
        ],
    }


def _game(pairing: dict, match: dict, entries: dict) -> dict:
    return {
        "match_id": str(pairing["match_id"]),
        "board": pairing["board"],
        "white": league_bot(entries[pairing["white"]]),
        "black": league_bot(entries[pairing["black"]]),
        "status": match["status"],
        "result": match.get("result"),
        "termination": match.get("termination"),
    }
