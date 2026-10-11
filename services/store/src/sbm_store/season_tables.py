"""The tables of a started season, computed from its matches (E135)."""

from dataclasses import dataclass

from pymongo.database import Database

from sbm_store import league_table
from sbm_store.matches import ABORTED, FINISHED
from sbm_store.names import MATCHES

PROJECTION = {
    "white.bot_id": 1,
    "white.user_id": 1,
    "black.bot_id": 1,
    "black.user_id": 1,
    "status": 1,
    "result": 1,
    "termination": 1,
    "context.tier": 1,
    "ply_count": {"$size": "$moves"},
}


@dataclass
class TierTable:
    tier: int
    games: int
    finished: int
    rows: list[league_table.Row]


def tables(db: Database, season: dict, *, tier: int | None = None) -> list[TierTable]:
    """One table per tier with the counts of its games, or only the one of tier; empty before
    the start."""
    query: dict = {"context.season_id": season["_id"]}
    if tier is not None:
        query["context.tier"] = tier
    by_tier: dict[int, list[dict]] = {}
    for match in db[MATCHES].find(query, PROJECTION):
        by_tier.setdefault(match["context"]["tier"], []).append(match)
    settings = season["settings"]
    result = []
    for lineup in season["tiers"]:
        if tier is not None and lineup["tier"] != tier:
            continue
        games = by_tier.get(lineup["tier"], [])
        rows = league_table.table(
            lineup["entries"],
            league_table.counted_games(games),
            points=settings["points"],
            tiebreaks=settings["tiebreaks"],
            withdrawn=season["withdrawn"],
        )
        ended = sum(game["status"] in (FINISHED, ABORTED) for game in games)
        result.append(TierTable(lineup["tier"], len(games), ended, rows))
    return result
