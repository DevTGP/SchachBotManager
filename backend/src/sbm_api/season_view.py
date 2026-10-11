"""A season with its tables as the API shows it (schema Season, E135, E137).

A running season computes its tables from its matches; a finished one shows the final tables
it stored, with the outcomes, and the counts of its matches.
"""

from pymongo.database import Database
from sbm_store import leagues, season_tables, seasons

from sbm_api.league_view import league_bot, settings_view
from sbm_api.match_view import discipline
from sbm_api.timestamps import optional_timestamp


def season_view(db: Database, season: dict) -> dict:
    settings = season["settings"]
    league = leagues.get(db, season["league_id"])
    # The name at the start; before it the league's current name.
    if settings is not None:
        league_name = settings["league_name"]
    else:
        league_name = "?" if league is None else league["name"]
    return {
        "id": str(season["_id"]),
        "league_id": str(season["league_id"]),
        "league_name": league_name,
        "number": season["number"],
        "status": season["status"],
        "starts_after": optional_timestamp(season["starts_after"]),
        "started_at": optional_timestamp(season["started_at"]),
        "finished_at": optional_timestamp(season["finished_at"]),
        "settings": None if settings is None else settings_view(settings),
        "discipline": None if settings is None else discipline(settings["discipline_snapshot"]),
        "tiers": _tiers(db, season) if settings is not None else [],
    }


def _tiers(db: Database, season: dict) -> list[dict]:
    final = {tier["tier"]: tier["table"] for tier in season["final"] or []}
    result = []
    for table in season_tables.tables(db, season):
        if season["status"] == seasons.FINISHED and table.tier in final:
            rows = final[table.tier]
        else:
            rows = [row.to_document() for row in table.rows]
        result.append(
            {
                "tier": table.tier,
                "games": table.games,
                "finished": table.finished,
                "table": [_row(row) for row in rows],
            }
        )
    return result


def _row(row: dict) -> dict:
    return row | {"bot": league_bot(row["bot"])}
