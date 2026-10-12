"""Starting due seasons and laying out their schedule (E132–E134); the runner calls this.

The start fixes the lineup in one write; the schedule follows and is confirmed with scheduled.
Laying it out again after a crash adds only the games and jobs still missing, so it can repeat.
Only the games of each tier's current round get jobs; hand_out gives the next round its jobs
once the previous one has ended (E187).
"""

import random
from datetime import datetime

from bson import ObjectId
from pymongo.database import Database

from sbm_store import (
    competition_entrants,
    competition_pace,
    disciplines,
    jobs,
    leagues,
    matches,
    participants,
    registrations,
    seasons,
)
from sbm_store.discipline import Discipline
from sbm_store.league_lineup import candidates, lineup
from sbm_store.league_pairing import schedule as round_robin
from sbm_store.names import MATCHES

LOT_RANGE = 2**31


def start_due(db: Database, now: datetime, rng: random.Random | None = None) -> list[ObjectId]:
    """Starts each due season that has enough participants; returns the ids of those started."""
    rng = rng or random.Random()
    started = []
    for season in seasons.due(db, now):
        league = leagues.get(db, season["league_id"])
        if league is None or league["archived"]:
            continue
        discipline = disciplines.get(db, league["discipline_id"])
        if discipline is None:
            continue
        tiers = _lineup(db, league, season, rng)
        if sum(len(tier["entries"]) for tier in tiers) < max(2, league["min_participants"]):
            continue
        settings = leagues.settings(league) | {
            "league_name": league["name"],
            "discipline_snapshot": disciplines.snapshot(discipline).to_document(),
        }
        running = seasons.begin(db, season["_id"], settings=settings, tiers=tiers, now=now)
        if running is not None:
            lay_out(db, running, now)
            started.append(running["_id"])
    return started


def lay_out_pending(db: Database, now: datetime) -> int:
    """Lays out the schedule of running seasons a crash left without one; returns how many."""
    pending = [season for season in seasons.running(db) if not season["scheduled"]]
    for season in pending:
        lay_out(db, season, now)
    return len(pending)


def hand_out(db: Database, now: datetime) -> int:
    """Gives the bot games of the current rounds of running seasons their jobs (E187);
    returns how many jobs were added."""
    return sum(
        _add_jobs(db, season, season["settings"]["priority"], now)
        for season in seasons.running(db)
        if season["scheduled"]
    )


def lay_out(db: Database, season: dict, now: datetime) -> None:
    """Stores the missing games of the season and the missing jobs of its waiting games."""
    settings = season["settings"]
    discipline = Discipline.from_document(settings["discipline_snapshot"])
    existing = {
        _place(match["context"])
        for match in db[MATCHES].find({"context.season_id": season["_id"]}, {"context": 1})
    }
    games = []
    for tier in season["tiers"]:
        for pairing in round_robin(tier["entries"], settings["games_per_pairing"]):
            games.append((pairing.round, tier["tier"], pairing.board + 1, pairing))
    new = []
    for round_number, tier, board, pairing in sorted(games, key=lambda game: game[:3]):
        if (tier, round_number, board) in existing:
            continue
        context = matches.league_context(
            season, settings["league_name"], tier=tier, round_number=round_number, board=board
        )
        new.append(
            matches.new_league_match(
                _side(pairing.white),
                _side(pairing.black),
                discipline,
                context=context,
                priority=settings["priority"],
                now=now,
            )
        )
    if new:
        db[MATCHES].insert_many(new)
    _add_jobs(db, season, settings["priority"], now)
    seasons.mark_scheduled(db, season["_id"])


def _lineup(db: Database, league: dict, season: dict, rng: random.Random) -> list[dict]:
    """Bots and accounts alike, by their keys (E182)."""
    registered = registrations.active_of_league(db, league["_id"])
    waiting = [participants.key(entry) for entry in registered]
    eligible = competition_entrants.eligible(db, registered)
    order = candidates(season["seeds"], waiting, set(eligible))
    cut = lineup(order, tiers=league["tiers"], tier_size=league["tier_size"])
    return [
        {"tier": number, "entries": [_entry(eligible[key], rng) for key in tier]}
        for number, tier in enumerate(cut, start=1)
    ]


def _entry(fields: dict, rng: random.Random) -> dict:
    return fields | {"lot": rng.randrange(LOT_RANGE)}


def _side(entry: dict) -> dict:
    """A season entry as matches.side takes it; an account keeps its user_id."""
    return {
        "_id": participants.key(entry),
        "user_id": entry.get("user_id"),
        "name": entry["name"],
        "version": entry["version"],
    }


def _place(context: dict) -> tuple:
    return context["tier"], context["round"], context["board"]


def _add_jobs(db: Database, season: dict, priority: int, now: datetime) -> int:
    """Jobs for the waiting bot games of each tier's current round (E187); a game with an
    account waits for its readiness instead (E183)."""
    competition = jobs.league_competition(season["league_id"])
    return sum(
        competition_pace.add_round_jobs(
            db,
            {"context.season_id": season["_id"], "context.tier": tier["tier"]},
            competition=competition,
            priority=priority,
            now=now,
        )
        for tier in season["tiers"]
    )
