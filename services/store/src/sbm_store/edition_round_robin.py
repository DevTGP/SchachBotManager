"""The plan of a round robin edition (E174): every game laid out at the start.

The rounds follow the circle method of the leagues (league_pairing); each game names its match id
up front, so the games can be stored in a second step that may repeat.
"""

from bson import ObjectId

from sbm_store.league_pairing import schedule


def plan(participants: list[dict], games_per_pairing: int) -> dict:
    """{rounds: [{round, bye, pairings: [{board, white, black, match_id}]}]}; bye is the bot
    that sits a round out when the number is odd."""
    bot_ids = [entry["bot_id"] for entry in participants]
    rounds: dict[int, list[dict]] = {}
    for pairing in schedule(bot_ids, games_per_pairing):
        rounds.setdefault(pairing.round, []).append(
            {
                "board": pairing.board + 1,
                "white": pairing.white,
                "black": pairing.black,
                "match_id": ObjectId(),
            }
        )
    result = []
    for number, pairings in sorted(rounds.items()):
        playing = {bot for each in pairings for bot in (each["white"], each["black"])}
        resting = [bot_id for bot_id in bot_ids if bot_id not in playing]
        result.append(
            {"round": number, "bye": resting[0] if resting else None, "pairings": pairings}
        )
    return {"rounds": result}
