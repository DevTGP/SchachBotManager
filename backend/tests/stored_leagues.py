"""Leagues and their seasons written through the store for the tests (E131–E136)."""

import random
from datetime import timedelta

from sbm_store import (
    competition_entrants,
    league_setup,
    leagues,
    registrations,
    season_start,
    seasons,
)

from stored_disciplines import store_discipline
from stored_games import NOW


def store_league(db, name: str = "Liga", discipline: dict | None = None, **settings) -> dict:
    if discipline is None:
        discipline = store_discipline(db, f"{name} Blitz")
    fields = {"name": name, "discipline_id": discipline["_id"]} | settings
    league = leagues.new_league(fields, created_by=None, now=NOW)
    assert league_setup.create(db, league, NOW)
    return league


def register(db, league: dict, entrants: list[dict]) -> None:
    """entrants are bot or account documents (E182)."""
    for holder in entrants:
        fields = competition_entrants.fields(holder)
        entry = registrations.new_registration(
            league["_id"], fields["bot_id"], user_id=fields["user_id"], created_by=None, now=NOW
        )
        assert registrations.insert(db, entry)


def start_season(db, league: dict, entrants: list[dict]) -> dict:
    """Registers the bots or accounts, releases the first season and starts it; returns it."""
    register(db, league, entrants)
    assert league_setup.start(db, league["_id"], NOW)
    started = season_start.start_due(db, NOW + timedelta(seconds=1), random.Random(1))
    assert started
    return seasons.latest(db, league["_id"])
