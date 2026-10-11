"""Finishing seasons whose games have all ended (E132, E133, E135); the runner calls this.

The next season is stored before the old one is marked finished: a crash in between finishes
the old one again on the next round, and the next season's unique number stops a second copy.
"""

from datetime import datetime, timedelta

from bson import ObjectId
from pymongo.database import Database

from sbm_store import leagues, matches, season_tables, seasons
from sbm_store.league_lineup import moves
from sbm_store.names import MATCHES


def finish_done(db: Database, now: datetime) -> list[ObjectId]:
    """Finishes each scheduled season without waiting or running games; returns their ids."""
    finished = []
    for season in seasons.running(db):
        if season["scheduled"] and not _open(db, season["_id"]):
            finish(db, season, now)
            finished.append(season["_id"])
    return finished


def finish(db: Database, season: dict, now: datetime) -> None:
    settings = season["settings"]
    tables = season_tables.tables(db, season)
    seeds, outcomes = moves(
        [[(row.bot_id, row.withdrawn) for row in table.rows] for table in tables],
        promotions=settings["promotions"],
        tier_size=settings["tier_size"],
    )
    final = []
    for table in tables:
        for row in table.rows:
            row.outcome = outcomes[row.bot_id]
        final.append({"tier": table.tier, "table": [row.to_document() for row in table.rows]})
    league = leagues.get(db, season["league_id"]) or settings
    starts_after = now + timedelta(minutes=league["pause_minutes"])
    following = seasons.new_season(
        season["league_id"], season["number"] + 1, starts_after=starts_after, seeds=seeds, now=now
    )
    seasons.insert(db, following)
    seasons.finish(db, season["_id"], final, now)


def _open(db: Database, season_id: ObjectId) -> bool:
    query = {"context.season_id": season_id, "status": {"$in": [matches.QUEUED, matches.RUNNING]}}
    return db[MATCHES].count_documents(query, limit=1) > 0
