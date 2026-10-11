"""The seasons a bot version played in, with its place there (E139)."""

from dataclasses import dataclass

from bson import ObjectId
from pymongo import DESCENDING
from pymongo.database import Database

from sbm_store import season_tables, seasons
from sbm_store.names import SEASONS


@dataclass
class BotSeason:
    season: dict
    tier: int
    tier_size: int
    # The bot's row of the tier's table (league_table.Row.to_document): the final one once the
    # season has finished, the current one while it runs.
    row: dict


def of_bot(db: Database, bot_id: ObjectId) -> list[BotSeason]:
    """The started seasons with the bot in their lineup, newest first."""
    query = {
        "tiers.entries.bot_id": bot_id,
        "status": {"$in": [seasons.RUNNING, seasons.FINISHED]},
    }
    found = db[SEASONS].find(query).sort([("started_at", DESCENDING), ("_id", DESCENDING)])
    result = []
    for season in found:
        tier = seasons.tier_of(season, bot_id)
        assert tier is not None
        entries = next(each["entries"] for each in season["tiers"] if each["tier"] == tier)
        rows = _rows(db, season, tier)
        row = next(row for row in rows if row["bot"]["bot_id"] == bot_id)
        result.append(BotSeason(season, tier, len(entries), row))
    return result


def _rows(db: Database, season: dict, tier: int) -> list[dict]:
    if season["status"] == seasons.FINISHED:
        for final in season["final"] or []:
            if final["tier"] == tier:
                return final["table"]
    (table,) = season_tables.tables(db, season, tier=tier)
    return [row.to_document() for row in table.rows]
