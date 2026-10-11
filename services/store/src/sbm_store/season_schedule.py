"""The schedule of one tier of a season by rounds and boards (E138)."""

from dataclasses import dataclass

from pymongo.database import Database

from sbm_store import participants
from sbm_store.names import MATCHES

PROJECTION = {
    "white": 1,
    "black": 1,
    "status": 1,
    "result": 1,
    "termination": 1,
    "context.round": 1,
    "context.board": 1,
}


@dataclass
class Round:
    number: int
    games: list[dict]
    # The tier's entry without a game in this round when the tier has an odd number of bots.
    bye: dict | None


def rounds(db: Database, season: dict, tier: int) -> list[Round] | None:
    """The rounds in order, each with its games by board; None if the season has no such tier
    (yet). A round whose games were all deleted with a bot (E105) is left out."""
    entries = next((each["entries"] for each in season["tiers"] if each["tier"] == tier), None)
    if entries is None:
        return None
    query = {"context.season_id": season["_id"], "context.tier": tier}
    by_round: dict[int, list[dict]] = {}
    for match in db[MATCHES].find(query, PROJECTION):
        by_round.setdefault(match["context"]["round"], []).append(match)
    result = []
    for number, games in sorted(by_round.items()):
        games.sort(key=lambda game: game["context"]["board"])
        result.append(Round(number, games, _bye(entries, games)))
    return result


def _bye(entries: list[dict], games: list[dict]) -> dict | None:
    if len(entries) % 2 == 0:
        return None
    playing = {participants.key(game[color]) for game in games for color in participants.COLORS}
    idle = [entry for entry in entries if participants.key(entry) not in playing]
    return idle[0] if len(idle) == 1 else None
