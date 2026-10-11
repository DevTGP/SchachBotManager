"""The schedule of one tier of a season as the API shows it (schema SeasonSchedule, E138)."""

from sbm_store.season_schedule import Round

from sbm_api.participant_view import participant


def schedule_view(tier: int, rounds: list[Round]) -> dict:
    return {"tier": tier, "rounds": [_round(each) for each in rounds]}


def _round(each: Round) -> dict:
    return {
        "round": each.number,
        "bye": None if each.bye is None else participant(each.bye),
        "games": [_game(game) for game in each.games],
    }


def _game(game: dict) -> dict:
    return {
        "match_id": str(game["_id"]),
        "board": game["context"]["board"],
        "white": participant(game["white"]),
        "black": participant(game["black"]),
        "status": game["status"],
        "result": game.get("result"),
        "termination": game.get("termination"),
    }
