"""A season of one bot version as the API shows it (schema BotSeason, E139)."""

from sbm_store.bot_seasons import BotSeason

from sbm_api.timestamps import optional_timestamp, timestamp


def bot_season_view(found: BotSeason) -> dict:
    season, row = found.season, found.row
    return {
        "season_id": str(season["_id"]),
        "league_id": str(season["league_id"]),
        "league_name": season["settings"]["league_name"],
        "number": season["number"],
        "status": season["status"],
        "started_at": timestamp(season["started_at"]),
        "finished_at": optional_timestamp(season["finished_at"]),
        "tier": found.tier,
        "rank": row["rank"],
        "tier_size": found.tier_size,
        "games": row["games"],
        "points": row["points"],
        "withdrawn": row["withdrawn"],
        "outcome": row["outcome"],
    }
