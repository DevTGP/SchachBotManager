"""The schedule of one tier of a season as the API shows it (schema SeasonSchedule, E138)."""

from sbm_store.season_schedule import Round

from sbm_api.league_view import league_bot


def schedule_view(tier: int, rounds: list[Round]) -> dict:
    return {"tier": tier, "rounds": [_round(each) for each in rounds]}


def _round(each: Round) -> dict:
    return {
        "round": each.number,
        "bye": None if each.bye is None else league_bot(each.bye),
        "games": [_game(game) for game in each.games],
    }


def _game(game: dict) -> dict:
    return {
        "match_id": str(game["_id"]),
        "board": game["context"]["board"],
        "white": league_bot(game["white"]),
        "black": league_bot(game["black"]),
        "status": game["status"],
        "result": game.get("result"),
        "termination": game.get("termination"),
    }
